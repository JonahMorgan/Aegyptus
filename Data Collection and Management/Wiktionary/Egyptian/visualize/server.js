const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8000;

// MIME types
const mimeTypes = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon'
};

const server = http.createServer((req, res) => {
    console.log(`${req.method} ${req.url}`);
    
    // Redirect root to index.html
    let filePath = req.url === '/' ? '/index.html' : req.url;
    
    // Remove query string if present
    filePath = filePath.split('?')[0];
    
    // Build full file path
    filePath = path.join(__dirname, filePath);
    
    // Get file extension
    const extname = String(path.extname(filePath)).toLowerCase();
    const contentType = mimeTypes[extname] || 'application/octet-stream';
    
    // Read and serve file
    fs.readFile(filePath, (error, content) => {
        if (error) {
            if (error.code === 'ENOENT') {
                // File not found - try parent directory for lemma_networks.json
                if (req.url.includes('lemma_networks.json')) {
                    const parentPath = path.join(__dirname, '..', 'lemma_networks.json');
                    fs.readFile(parentPath, (err, data) => {
                        if (err) {
                            res.writeHead(404, { 'Content-Type': 'text/html' });
                            res.end('<h1>404 - File Not Found</h1>', 'utf-8');
                        } else {
                            res.writeHead(200, { 'Content-Type': 'application/json' });
                            res.end(data, 'utf-8');
                        }
                    });
                } else {
                    res.writeHead(404, { 'Content-Type': 'text/html' });
                    res.end('<h1>404 - File Not Found</h1>', 'utf-8');
                }
            } else {
                res.writeHead(500);
                res.end(`Server Error: ${error.code}`, 'utf-8');
            }
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
});

server.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}/`);
    console.log(`Press Ctrl+C to stop`);
});
