let mut i:i32;
let mut n:i32;
let mut f:i32 = 1;
n = scanln!();
i = 2;
while (i < n + 1) {
  f = f * i;
  i = i + 1;
}
println!(f);
