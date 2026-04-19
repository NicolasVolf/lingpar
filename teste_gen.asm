section .data
  format_out: db "%d", 10, 0
  format_in: db "%d", 0
  scan_int: dd 0

section .text
  extern printf
  extern scanf
  global _start

_start:
  push ebp
  mov ebp, esp

  sub esp, 4 ; var i i32
  sub esp, 4 ; var n i32
  sub esp, 4 ; var f i32
  mov eax, 1
  mov [ebp-12], eax
  push scan_int
  push format_in
  call scanf
  add esp, 8
  mov eax, dword [scan_int]
  mov [ebp-8], eax
  mov eax, 2
  mov [ebp-4], eax
  loop_33:
  mov eax, 1
  push eax
  mov eax, [ebp-8]
  pop ecx
  add eax, ecx
  push eax
  mov eax, [ebp-4]
  pop ecx
  cmp eax, ecx
  mov eax, 0
  mov ecx, 1
  cmovl eax, ecx
  cmp eax, 0
  je exit_33
  mov eax, [ebp-4]
  push eax
  mov eax, [ebp-12]
  pop ecx
  imul ecx
  mov [ebp-12], eax
  mov eax, 1
  push eax
  mov eax, [ebp-4]
  pop ecx
  add eax, ecx
  mov [ebp-4], eax
  jmp loop_33
  exit_33:
  mov eax, [ebp-12]
  push eax
  push format_out
  call printf
  add esp, 8
  mov esp, ebp
  pop ebp

  mov eax, 1
  xor ebx, ebx
  int 0x80
