const http = require('http');

const server = http.createServer((req, res) => {
    const body = [];
    req.on('data', chunk => body.push(chunk));
    req.on('end', () => {
        const response = {
            status: 'ok',
            method: req.method,
            path: req.url,
            headers: req.headers,
            body: body.length > 0 ? Buffer.concat(body).toString() : null,
            timestamp: new Date().toISOString(),
        };

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(response, null, 2));
    });
});

const PORT = process.env.PORT || 8080;
server.listen(PORT, () => {
    console.log(`Mock API server running on port ${PORT}`);
});
