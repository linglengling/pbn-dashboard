const body = {
    site_domain: 'testpbn.group',
    target_url: 'http://localhost:3000/ddd',
    anchor_text: 'day la test',
    location: 'homepage'
};

console.log("Sending POST to http://localhost:3000/api/backlinks/insert...");

fetch('http://localhost:3000/api/backlinks/insert', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
})
.then(async res => {
    console.log("Status:", res.status);
    const text = await res.text();
    console.log("Response:", text);
})
.catch(err => console.error("Error:", err));
