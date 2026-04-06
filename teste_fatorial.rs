i = 1;
n = 5;
f = 1;
if (n < 2) {
    f = 1;
} else {
    while (i < n || i == n) {
        f = f * i;
        i = i + 1;
    }
}
println!(f);
