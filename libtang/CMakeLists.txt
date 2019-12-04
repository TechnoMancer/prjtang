cmake_minimum_required(VERSION 3.5)
project(libtang)

option(BUILD_PYTHON "Build Python Integration" ON)
option(BUILD_SHARED "Build shared Tang library" ON)
option(STATIC_BUILD "Create static build of Tang tools" OFF)

set(CMAKE_CXX_STANDARD 14)
if (MSVC)
    set(CMAKE_CXX_FLAGS "-bigobj -EHsc")
else()
    set(CMAKE_CXX_FLAGS "-Wall -pedantic -Wextra -O3 -g")
endif()
set(CMAKE_DEFIN)
set(link_param "")
if (STATIC_BUILD)
    set(Boost_USE_STATIC_LIBS ON)
    if(MSVC)
        add_definitions(-DBOOST_PYTHON_STATIC_LIB)
        set(CMAKE_CXX_FLAGS_RELEASE "/MT")
        set(CMAKE_CXX_FLAGS_DEBUG "/MTd")
    elseif (NOT APPLE)
        set(link_param "-static")
    endif()
else()
    if(MSVC)
        set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
    endif()
endif()
set(boost_libs filesystem thread program_options)
set(Boost_NO_BOOST_CMAKE ON)
find_package(PythonInterp 3.5 REQUIRED)

if (BUILD_PYTHON)
    find_package(PythonLibs 3.5 REQUIRED)
endif()

find_package(Boost REQUIRED COMPONENTS ${boost_libs})

if (BUILD_PYTHON)
    # Find Boost::Python of a suitable version in a cross-platform way
    # Some distributions (Arch) call it libboost_python3, others such as Ubuntu
    # call it libboost_python35. In the latter case we must consider all minor versions
    # Original source: https://github.com/BVLC/caffe/blob/master/cmake/Dependencies.cmake#L148
    set(version ${PYTHONLIBS_VERSION_STRING})

    STRING(REGEX REPLACE "[^0-9]" "" boost_py_version "${version}")
    find_package(Boost QUIET COMPONENTS "python-py${boost_py_version}" ${boost_libs})
    set(Boost_PYTHON_FOUND ${Boost_PYTHON-PY${boost_py_version}_FOUND})

    while (NOT "${version}" STREQUAL "" AND NOT Boost_PYTHON_FOUND)
        STRING(REGEX REPLACE "([0-9.]+).[0-9]+" "\\1" version "${version}")

        STRING(REGEX REPLACE "[^0-9]" "" boost_py_version "${version}")
        find_package(Boost QUIET COMPONENTS "python-py${boost_py_version}" ${boost_libs})
        set(Boost_PYTHON_FOUND ${Boost_PYTHON-PY${boost_py_version}_FOUND})

        STRING(REGEX MATCHALL "([0-9.]+).[0-9]+" has_more_version "${version}")
        if ("${has_more_version}" STREQUAL "")
            break()
        endif ()
    endwhile ()

    if (NOT Boost_PYTHON_FOUND)
        foreach (PyVer 3 36 37 38)
            find_package(Boost QUIET COMPONENTS python${PyVer} ${boost_libs})
            if ("${Boost_LIBRARIES}" MATCHES ".*(python|PYTHON).*" )
                set(Boost_PYTHON_FOUND TRUE)
                break()
            endif ()
        endforeach ()
    endif ()

    if (NOT Boost_PYTHON_FOUND)
        STRING(REGEX REPLACE "([0-9]+\\.[0-9]+).*" "\\1" gentoo_version "${PYTHONLIBS_VERSION_STRING}")
        find_package(Boost QUIET COMPONENTS python-${gentoo_version} ${boost_libs})
        if ("${Boost_LIBRARIES}" MATCHES ".*(python|PYTHON).*" )
            set(Boost_PYTHON_FOUND TRUE)
        endif ()
    endif ()

    if (NOT Boost_PYTHON_FOUND )
        message( FATAL_ERROR "No version of Boost::Python 3.x could be found.")
    endif ()
endif()

include_directories(include/ ${Boost_INCLUDE_DIRS} ${PYTHON_INCLUDE_DIRS})

aux_source_directory(include/ INCLUDE_FILES)
aux_source_directory(src/ SOURCE_FILES)

if (BUILD_SHARED)
    add_library(tang SHARED ${INCLUDE_FILES} ${SOURCE_FILES})
else()
    add_library(tang STATIC ${INCLUDE_FILES} ${SOURCE_FILES})
endif()

target_link_libraries(tang LINK_PUBLIC ${Boost_LIBRARIES} ${CMAKE_THREAD_LIBS_INIT})
if (BUILD_PYTHON)
    target_link_libraries(tang LINK_PUBLIC ${PYTHON_LIBRARIES})
endif()

if (BUILD_PYTHON)
    PYTHON_ADD_MODULE(pytang ${INCLUDE_FILES} ${SOURCE_FILES})
    target_compile_definitions(pytang PRIVATE INCLUDE_PYTHON=1)
    target_link_libraries(pytang LINK_PUBLIC ${Boost_LIBRARIES} ${PYTHON_LIBRARIES})
endif()

include(GNUInstallDirs)

file(RELATIVE_PATH TANG_RPATH_LIBDIR /${CMAKE_INSTALL_BINDIR} /${CMAKE_INSTALL_LIBDIR})
file(RELATIVE_PATH TANG_RPATH_DATADIR /${CMAKE_INSTALL_BINDIR} /${CMAKE_INSTALL_DATADIR})

function(setup_rpath name)
    if(APPLE)
        set_target_properties(${name} PROPERTIES
                              BUILD_WITH_INSTALL_RPATH ON
                              INSTALL_RPATH "@loader_path/${TANG_RPATH_LIBDIR}/tang"
                              INSTALL_NAME_DIR "@rpath")
    elseif(UNIX)
        set_target_properties(${name} PROPERTIES
                              BUILD_WITH_INSTALL_RPATH ON
                              INSTALL_RPATH "\$ORIGIN/${TANG_RPATH_LIBDIR}/tang")
    endif()
endfunction()

# Avoid perturbing build if git version hasn't changed
file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/generated")
set(LAST_GIT_VERSION "")
if (NOT DEFINED CURRENT_GIT_VERSION)
    execute_process(COMMAND git describe --tags OUTPUT_VARIABLE CURRENT_GIT_VERSION)
endif()
string(STRIP "${CURRENT_GIT_VERSION}" CURRENT_GIT_VERSION)
if (EXISTS "${CMAKE_BINARY_DIR}/generated/last_git_version")
    file(READ "${CMAKE_BINARY_DIR}/generated/last_git_version" LAST_GIT_VERSION)
endif()
if (NOT ("${LAST_GIT_VERSION}" STREQUAL "${CURRENT_GIT_VERSION}"))
    configure_file(
      ${CMAKE_SOURCE_DIR}/tools/version.cpp.in
      ${CMAKE_BINARY_DIR}/generated/version.cpp
    )
endif()
file(WRITE "${CMAKE_BINARY_DIR}/generated/last_git_version" CURRENT_GIT_VERSION)

add_executable(tangbit ${INCLUDE_FILES} tools/tangbit.cpp "${CMAKE_BINARY_DIR}/generated/version.cpp")
target_include_directories(tangbit PRIVATE tools)
target_compile_definitions(tangbit PRIVATE TANG_RPATH_DATADIR="${TANG_RPATH_DATADIR}" TANG_PREFIX="${CMAKE_INSTALL_PREFIX}")
target_link_libraries(tangbit tang ${Boost_LIBRARIES} ${CMAKE_DL_LIBS} ${link_param})
setup_rpath(tangbit)

if (BUILD_SHARED)
    install(TARGETS tang tangbit pytang
            LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}/tang
            RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
else()
    install(TARGETS tangbit
            RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
endif()
install(DIRECTORY ../database DESTINATION ${CMAKE_INSTALL_DATADIR}/tang PATTERN ".git" EXCLUDE)

file(GLOB_RECURSE CLANGFORMAT_FILES *.cpp *.hpp)

add_custom_target(
    clangformat
    COMMAND clang-format
    -style=file
    -i
    ${CLANGFORMAT_FILES}
)
