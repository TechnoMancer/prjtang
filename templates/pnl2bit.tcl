import_device ${part}.db -package ${package}
read_pnl ${pnl_file}
bitgen -bit "${bit_file}" -version 0X00 -g ucode:00000000000000000000000000000000 -info -log_file "${bit_file}.log"
