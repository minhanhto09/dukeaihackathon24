document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('generateBtn').addEventListener('click', function() {
        const calendarFile = document.getElementById('calendarFile').files[0];
        const healthFile = document.getElementById('healthFile').files[0];

        if (calendarFile && healthFile) {
            // Process the files
            const output = document.getElementById('output');
            output.innerText = `Files Selected: ${calendarFile.name}, ${healthFile.name}`;
        } else {
            alert('Please select both files.');
        }
    });
});
