import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [jobUrl, setJobUrl] = useState('https://www.workatastartup.com/jobs/66658');
  const [linkedinUrl, setLinkedinUrl] = useState('https://www.linkedin.com/in/seth-donaldson/');
  const [resumeFile, setResumeFile] = useState(null);
  const [coverLetter, setCoverLetter] = useState('');
  const [logs, setLogs] = useState('');
  const [loading, setLoading] = useState(false);
  const loadingRef = useRef(loading);
  const textareaCrewOutputRef = useRef(null);

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

  const setLoadingTrue = async () => {
    console.log("setting loading to true")
    setLoading(true);
  }

  const handleGenerateCoverLetter = async () => {
    const formData = new FormData();
    formData.append('jobUrl', jobUrl);
    formData.append('linkedinUrl', linkedinUrl);
    formData.append('resumeFile', resumeFile);

    const loadingSet = await setLoadingTrue();
    console.log(loadingSet);
    try {
      console.log("here")
      const response = await axios.post('http://localhost:5001/generate-cover-letter', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      console.log(response.data.coverLetter)
      setCoverLetter(response.data.coverLetter);
      setLoading(false);
    } catch (error) {
      console.error('Error generating cover letter:', error);
      setLoading(false);
    }
  };

  const handleFetchLogs = async () => {
    try {
      const response = await axios.get('http://localhost:5001/get-logs', { responseType: 'text' });
      setLogs(response.data);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  // Update the ref whenever `loading` changes
  useEffect(() => {
    loadingRef.current = loading;
  }, [loading]);
  
  // Hacky way to show what the backend is doing Fetch logs every 500ms
  useEffect(() => {
    const timer = setInterval(() => {
      console.log("loading: ", loadingRef.current)
      if (loadingRef.current) {
        handleFetchLogs();
      }
    }, 500);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (textareaCrewOutputRef.current) {
      textareaCrewOutputRef.current.scrollTop = textareaCrewOutputRef.current.scrollHeight;
    }
  }, [logs]);


  // todo: conditionaly render the logs textarea
  // todo: conditionaly render the areas for the candidate_profile, 
  //       job_requirements, cover_letter_review, and cover_letter sections
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
      <div className="status-group">
        <h2>Logs:</h2>
        <button onClick={setLoadingTrue}>Fetch Logs</button>
        <p>Loading: {loading.toString()}</p>
        <textarea ref={textareaCrewOutputRef} value={logs} readOnly />
      </div>
    </div>
  );
}

export default App;
