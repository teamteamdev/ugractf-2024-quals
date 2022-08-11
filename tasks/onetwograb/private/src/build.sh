emcc -O3 flag.c -o template.wasm --no-entry -s EXPORTED_FUNCTIONS="['_get_flag', '_get_flag_length']"
