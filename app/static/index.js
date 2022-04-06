//set the datetime minimum to current date, so can't schedule an event to never happen
const today = new Date().toISOString().slice(0, 16);
document.getElementsByName("event-date")[0].min = today;

/*
function deleteStudent(StudentNo){
    fetch('/delete_students', {
        method: 'POST',
        body: JSON.stringify({StudentNo: StudentNo}),
    }).then((_res) =>{
        window.location.href = "/";
});}
*/

