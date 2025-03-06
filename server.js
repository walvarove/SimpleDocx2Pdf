const express = require("express");
const multer = require("multer");
const { exec } = require("child-process-promise");
const fs = require("fs").promises;
const fsSync = require("fs");
const path = require("path");

const app = express();
const port = process.env.PORT || 3000;
const apiToken = process.env.API_TOKEN;

const storage = multer.memoryStorage(); // Store files in memory
const upload = multer({ storage: storage });

// API Token Middleware
const authenticateToken = (req, res, next) => {
  const token = req.headers["X-API-Token"];

  if (token == null) return res.sendStatus(401);

  if (token !== apiToken) return res.sendStatus(403);

  next();
};

app.post("/convert", authenticateToken, upload.single("docxFile"), async (req, res) => {
  if (!req.file) {
    return res.status(400).send("No file uploaded.");
  }

  try {
    const inputFilePath = path.join(__dirname, "data", req.file.originalname);
    const outputFilePath = path.join(__dirname, "data", path.parse(req.file.originalname).name + ".pdf");

    await fs.writeFile(inputFilePath, req.file.buffer);

    const libreofficeCommand = `libreoffice --headless --convert-to pdf --outdir ${path.join(__dirname, "data")} ${inputFilePath}`;
    await exec(libreofficeCommand);

    const pdfBuffer = await fs.readFile(outputFilePath);

    res.setHeader("Content-Type", "application/pdf");
    res.setHeader("Content-Disposition", `attachment; filename=${path.parse(req.file.originalname).name}.pdf`);
    res.send(pdfBuffer);

    // Clean up temporary files
    await fs.unlink(inputFilePath);
    await fs.unlink(outputFilePath);

  } catch (error) {
    console.error("Conversion error:", error);
    res.status(500).send("Conversion failed.");
  }
});

app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});