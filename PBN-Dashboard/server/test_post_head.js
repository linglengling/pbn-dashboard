const body = {
    site_domains: ['testpbn.group', 'pbnsite2.group'],
    head_code: '<link rel="hello" type="hello" title="testpbngroup" >'
};

console.log("Sending POST to http://localhost:3000/api/sites/update-head...");

fetch('http://localhost:3000/api/sites/update-head', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
})
.then(async res => {
    console.log("Status:", res.status);
    const text = await res.text();
    console.log("Raw Response:", text);
})
.catch(err => console.error("Network Error:", err));
