document.getElementById('convertBtn').addEventListener('click', function () {
    var stCode = document.getElementById('stCode').value;
    fetch('/convert', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ st_code: stCode })
    })
        .then(response => response.json())
        .then(data => {
            document.getElementById('convertedCode').value = data.converted_code;
        })
        .catch(error => {
            console.error('Error:', error);
        });
});