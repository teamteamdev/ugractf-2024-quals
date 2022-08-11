#include <stdio.h>
#include <stdlib.h>

#include <caml/memory.h>
#include <caml/mlvalues.h>

CAMLprim value caml_dumpmem(value fname, value start, value end) {
  CAMLparam3(fname, start, end);

  int err = 0;

  FILE* fptr = fopen(String_val(fname), "wb");
  if (fptr == NULL) {
    CAMLreturn(Val_int(-1));
  }

  void* ptr = (void*)Long_val(start);
  size_t size = (size_t)Long_val(end) - (size_t)Long_val(start);

  size_t readed = 0;
  while (readed < size) {
    readed += fwrite(ptr + readed, 1, size - readed, fptr);
    if (err = ferror(fptr)) {
      fclose(fptr);
      CAMLreturn(Val_int(err));
    }
  }

  if (err = fclose(fptr)) {
    CAMLreturn(Val_int(err));
  }

  CAMLreturn(Val_int(0));
}

CAMLprim value caml_addrof(value obj) {
  CAMLparam1(obj);
  CAMLreturn(Val_long((char*)obj));
}

CAMLprim value caml_trashify(value obj) {
  CAMLparam1(obj);
  value str = Field(obj, 0);
  size_t n = caml_string_length(str);
  unsigned char *ch = (unsigned char*) str;
  for (size_t i = 0; i < n; i++)
    ch[i] = i & 0xff;
  CAMLreturn(Val_unit);
}
