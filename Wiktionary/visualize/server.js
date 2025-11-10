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
    
    // Remove query string if present
    let filePath = req.url.split('?')[0];
    
    // Redirect root to index.html
    if (filePath === '/') {
        filePath = '/index.html';
    }
    
    // Special handling for JSON files - try parent directory first
    if (filePath.endsWith('.json')) {
        const jsonFileName = path.basename(filePath);
        const parentPath = path.join(__dirname, '..', jsonFileName);
        const currentPath = path.join(__dirname, jsonFileName);
        
        // Check if parent path is a directory
        fs.stat(parentPath, (statErr, stats) => {
            if (statErr || stats.isDirectory()) {
                // Parent path doesn't exist or is a directory, try current directory
                fs.readFile(currentPath, (err, data) => {
                    if (!err) {
                        console.log(`Serving ${jsonFileName} from current directory`);
                        res.writeHead(200, { 'Content-Type': 'application/json' });
                        res.end(data, 'utf-8');
                    } else {
                        res.writeHead(404, { 'Content-Type': 'text/html' });
                        res.end('<h1>404 - JSON File Not Found</h1>', 'utf-8');
                    }
                });
            } else {
                // Parent path exists and is a file
                fs.readFile(parentPath, (error, content) => {
                    if (!error) {
                        console.log(`Serving ${jsonFileName} from parent directory`);
                        res.writeHead(200, { 'Content-Type': 'application/json' });
                        res.end(content, 'utf-8');
                    } else {
                        // Try current directory as fallback
                        fs.readFile(currentPath, (err, data) => {
                            if (!err) {
                                console.log(`Serving ${jsonFileName} from current directory`);
                                res.writeHead(200, { 'Content-Type': 'application/json' });
                                res.end(data, 'utf-8');
                            } else {
                                res.writeHead(404, { 'Content-Type': 'text/html' });
                                res.end('<h1>404 - JSON File Not Found</h1>', 'utf-8');
                            }
                        });
                    }
                });
            }
        });
        return;
    }
    
    // Build full file path for other files
    filePath = path.join(__dirname, filePath);
    
    // Get file extension
    const extname = String(path.extname(filePath)).toLowerCase();
    const contentType = mimeTypes[extname] || 'application/octet-stream';
    
    // Read and serve file
    fs.readFile(filePath, (error, content) => {
        if (error) {
            if (error.code === 'ENOENT') {
                res.writeHead(404, { 'Content-Type': 'text/html' });
                res.end('<h1>404 - File Not Found</h1>', 'utf-8');
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
