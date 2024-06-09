import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';
import io from 'socket.io-client';
import { v4 as uuidv4 } from 'uuid';

function App() {
  const [jobUrl, setJobUrl] = useState('https://www.workatastartup.com/jobs/66658');
  const [linkedinUrl, setLinkedinUrl] = useState('https://www.linkedin.com/in/seth-donaldson/');
  const [resumeFile, setResumeFile] = useState(null);
  const [logs, setLogs] = useState('');
  const [taskId, setTaskId] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const textareaCrewOutputRef = useRef(null);
  const [coverLetter, setCoverLetter] = useState('');

  // Immediately start a session, the session ID is used to track the progress of the AI crew output
  useEffect(() => {
    let sessionId = sessionStorage.getItem('session_id');
    if (!sessionId) {
      sessionId = uuidv4();
      sessionStorage.setItem('session_id', sessionId);
      console.log('New session ID created:', sessionId);
    } else {
      console.log('Existing session ID found:', sessionId);
    }
    setSessionId(sessionId);
  }, []);

  // Listen for crew execution logs
  useEffect(() => {
    const socket = io('https://localhost:5001');  // Ensure this matches Flask-SocketIO setup
    socket.on('log', (data) => {
      setLogs((prevLogs) => prevLogs + '\n' + data.data);
    });

    return () => {
      socket.disconnect();
      console.log('Socket disconnected');
    };
  }, []);

  // todo: update to scroll to the bottom only IF the bar is already at the bottom
  // Scroll to the bottom whenever logs changes
  useEffect(() => {
    if (textareaCrewOutputRef.current) {
      textareaCrewOutputRef.current.scrollTop = textareaCrewOutputRef.current.scrollHeight;
    }
  }, [logs]);


  // Handlers
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

  const handleGenerateCoverLetter = async () => {
    const formData = new FormData();
    formData.append('jobUrl', jobUrl);
    formData.append('linkedinUrl', linkedinUrl);
    formData.append('resumeFile', resumeFile);

    // todo: ensure formData is correct, display popup/dialog if not

    try {
      console.log("here")
      const response = await axios.post('https://localhost:5001/generate-cover-letter-task', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'x-session-id': sessionId,
        }
      });
      console.log("taskId", response.data.task_id);
      setTaskId(response.data.task_id);
    } catch (error) {
      console.error('Error generating cover letter:', error);
    }
  };

  const handleCancelExecution = async () => {
    if (taskId) {
      try {
        await axios.post(`https://localhost:5001/cancel-task/${taskId}`);
        setTaskId(null);
      } catch (error) {
        console.error('Error canceling execution:', error);
      }
    }
  }

  useEffect(() => {
    const fetchTaskStatus = async () => {
      if (taskId) {
        try {
          const response = await axios.get(`https://localhost:5001/status/${taskId}`);
          const {state, status, result } = response.data;
          console.log(status);
          if (result) {
            setCoverLetter(result);
          }
          console.log();
          if (state === 'SUCCESS' || state === 'FAILURE') {
            setTaskId(null);
          }
        } catch (error) {
          console.error('Error fetching task status:', error);
          setTaskId(null);
        }
      }
    };
    const interval = setInterval(fetchTaskStatus, 500);
    return () => clearInterval(interval);
  }, [taskId]);

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
      <button onClick={handleGenerateCoverLetter}>Generate Cover Letter</button>
      <div className="output-group">
        <h2>Crew Execution</h2>
        <textarea ref={textareaCrewOutputRef} value={logs} readOnly />
      </div>
      <button onClick={handleCancelExecution}>Cancel Execution</button>
    </div>
  );
}

export default App;
