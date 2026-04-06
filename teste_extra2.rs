
n = scanln!;

a = 10;
b = 20;
if (a > 5 && b > 15) {
    println!(1);     
} else {
    println!(0);
}

x = 3;
if (x > 10 || x == 3) {
    println!(1);     
} else {
    println!(0);
}

flag = 0;
if (!flag) {
    println!(1);    
} else {
    println!(0);
}

i = 0;
while (i < 3 || i == 3) {
    println!(i);     
    i = i + 1;
}

j = 10;
while (j > 0 && j > 5) {
    println!(j);    
    j = j - 1;
}

k = 0;
while (!( k == 3 )) {
    println!(k);    
    k = k + 1;
}

i = 1;
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
