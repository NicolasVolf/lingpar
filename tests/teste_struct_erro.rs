// Caso de falha esperada: acessa um campo ("ages") que nao existe na struct
// ("age" e o nome correto). Deve lancar erro semantico ao rodar.
struct Student {
    let mut age: i32;
};

fn main() -> () {
    let student1: Student;
    student1.ages = 20;
}
