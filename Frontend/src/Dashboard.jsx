import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './App.css';

const Dashboard = () => {
  const [processingFileId, setProcessingFileId] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([
    { id: 1, name: 'SAMPLEPDF1.pdf' },
    { id: 2, name: 'SAMPLEPDF2.pdf' },
  ]);

  const handleUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const newFile = {
        id: uploadedFiles.length + 1,
        name: file.name,
        file: file,
      };
      setUploadedFiles([...uploadedFiles, newFile]);
    }
  };

  const handleDelete = (id) => {
    setUploadedFiles(uploadedFiles.filter((file) => file.id !== id));
  };

  const navigate = useNavigate();

  const handleProcess = async (file) => {
    const formData = new FormData();
    setProcessingFileId(file.id);

    try {
      formData.append('file', file.file);

      const response = await fetch('http://127.0.0.1:8000/process', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload Failed');
      const data = await response.json();
      navigate(`/chat/${file.id}`, {
        state: { filename: file.name },
      });
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setProcessingFileId(null);
    }
  };

  return (
    <div className="page">
      <div className="container">
        <h1 className="heading">Upload PDF, Docx or Excel files</h1>

        <div className="file-upload">
          <input
            type="file"
            accept=".pdf,.docx,.xlsx"
            onChange={handleUpload}
          />
        </div>


        <div className="table-wrapper">
          <table className="file-table">
            <thead>
              <tr>
                <th>File Name</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {uploadedFiles.map((file) => (
                <tr key={file.id}>
                  <td>{file.name}</td>
                  <td>
                    <div className="actions">
                      <button className="btn btn-delete" onClick={() => handleDelete(file.id)}>
                        Delete
                      </button>
                      <button
                        className="btn btn-process"
                        onClick={() => handleProcess(file)}
                        disabled={processingFileId === file.id}
                      >
                        {processingFileId === file.id ? (
                          <>
                            <svg
                              className="loading-icon"
                              xmlns="http://www.w3.org/2000/svg"
                              fill="none"
                              viewBox="0 0 24 24"
                            >
                              <circle
                                className="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                strokeWidth="4"
                              />
                              <path
                                className="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 11-8 8z"
                              />
                            </svg>
                            Processing...
                          </>
                        ) : (
                          'Process'
                        )}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {uploadedFiles.length === 0 && (
                <tr>
                  <td colSpan="2" className="empty-msg">
                    No files uploaded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
