import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [jobUrl, setJobUrl] = useState('');
  const [linkedinUrl, setLinkedinUrl] = useState('');
  const [resumeFile, setResumeFile] = useState(null);
  const [coverLetter, setCoverLetter] = useState('');

  const handleJobUrlChange = (e) => {
    setJobUrl(e.target.value);
    console.log(e.target.value);
  };

  const handleLinkedinUrlChange = (e) => {
    setLinkedinUrl(e.target.value);
  };

  const handleResumeFileChange = (e) => {
    setResumeFile(e.target.files[0]);
  };

  const checkCrewProgress = async() => {
    try {
      // This should take an optional parameter which is a list of files that have already been checked
      // (can be seen if their scrolly boxxes have been made already)
      const response = await axios.post('http://localhost:5001/check-crew-progress', {
        headers: {
          'Content-Type': 'text/html; charset=UTF-8'
        }
      });

      // This should be a list of titles / descriptions and their content

      // They should be looped through and a title / scrolly box should be made for each

    } catch (error) {
      console.error('Error generating cover letter:', error);
    }
  }

  const handleGenerateCoverLetter = async () => {
    const formData = new FormData();
    formData.append('jobUrl', jobUrl);
    formData.append('linkedinUrl', linkedinUrl);
    formData.append('resumeFile', resumeFile);

    try {
      console.log("here")
      const response = await axios.post('http://localhost:5001/generate-cover-letter', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      console.log(response.data.coverLetter)
      setCoverLetter(response.data.coverLetter);
    } catch (error) {
      console.error('Error generating cover letter:', error);
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      checkCrewProgress();
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="App">
      <h1>Cover Letter Generator</h1>
      <div className="input-group">
        <label>Job Posting URL:</label>
        <input type="text" value={jobUrl} onChange={handleJobUrlChange} />
      </div>
      <div className="input-group">
        <label>LinkedIn URL:</label>
        <input type="text" value={linkedinUrl} onChange={handleLinkedinUrlChange} />
      </div>
      <div className="input-group">
        <label>Resume PDF:</label>
        <input type="file" accept="application/pdf" onChange={handleResumeFileChange} />
      </div>
      <button onClick={handleGenerateCoverLetter}>Write Cover Letter</button>
      <div className="output-group">
        <h2>Generated Cover Letter:</h2>
        <textarea value={coverLetter} readOnly />
      </div>
    </div>
  );
}

export default App;
