// For implementation
n = 5;
y = 1;
i = 0;
for (i = 0; i < n; i = i + 1)
{
  y = y * (i + 1);
}
println!(if i == n { y } else { n });
println!(if i == n + 1 { y } else { n });
