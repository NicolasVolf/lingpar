let mut x: i32 = 3;
let mut n: i32 = if x > 2 { 5 } else { 3 };
let mut i: i32 = 0;

for (i = 0; i < n; i = i + 1) {
  println!(i);
}
