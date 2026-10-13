let students = [
    { id: 1, name: 'ali', program: 'Bachelor of Science Information Technology' },
    { id: 2, name: 'abi', program: 'Bachelor of Science Hospitality Management' },
    { id: 3, name: 'sandy', program: 'Bachelor of Science in Accountancy' },
    { id: 4, name: 'sam', program: 'Bachelor of Science in Nursing' },
    { id: 5, name: 'jen', program: 'Bachelor of Science in Computer Science' }
];

const createListItem = (student) => {
    // create element
    const article = document.createElement('article');
    const h2 = document.createElement('h2');
    const p = document.createElement('p');
    const button = document.createElement('button');

    // add value
    h2.innerText = student.name;
    p.innerText = student.program;
    button.innerText = 'Delete';

    // Delete Event Listener
    button.addEventListener('click', () => {

        students = students.filter((s) => s.id !== student.id);
        displayList();
    });

    // add class
    article.classList.add('list-item');

    // insert
    article.append(h2);
    article.append(p);
    article.append(button);

    return article;
};


const list = document.querySelector('#studentList');

const displayList = () => {
    list.replaceChildren();
    const studentList = students.map((s) => createListItem(s));
    studentList.forEach((s) => list.append(s));
};


displayList();


const form = document.querySelector('#studentForm');
const nameField = document.querySelector('#name');
const programField = document.querySelector('#program');

form.addEventListener('submit', (e) => {
    e.preventDefault();
    const name = nameField.value;
    const program = programField.value;


    const newStudent = {
        id: Date.now(),
        name,
        program
    };

    students.push(newStudent);
    nameField.value = '';
    programField.value = '';
    displayList();
});