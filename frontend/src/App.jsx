import React, { useState, useEffect, useRef } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import axios from 'axios';
import './App.css';
import io from 'socket.io-client';
import { v4 as uuidv4 } from 'uuid';


const OutputFile = ({title, fileName, onClick}) => {
  return (
    <div>
      {title}: <span style={{ color: 'blue', cursor: 'pointer' }} onClick={() => {onClick(fileName)}}>Download</span>
    </div>
  );
}

const OutputFiles = ({taskStatus, onClick}) => {
  if (taskStatus !== 'SUCCESS') {
    return <div></div>;
  } else {
    return (
      <div>
        <h2>Output Files</h2>
        <OutputFile title="Candidate Profile" fileName="candidate_profile.txt" onClick={onClick}/>
        <OutputFile title="Job Requirements" fileName="job_requirements.txt" onClick={onClick}/>
        <OutputFile title="Cover Letter Review" fileName="cover_letter_review.txt" onClick={onClick}/>
        <OutputFile title="Cover Letter" fileName="cover_letter.txt" onClick={onClick}/>
      </div>
    );
  }
}

const CrewOutput = ({crewOutputRef, logs, taskStatus}) => {
  if (taskStatus !== null) {
    return (
      <div className="output-group">
        <p>Generating cover letter...</p>
        <textarea ref={crewOutputRef} value={logs} readOnly />
      </div>
    );
  } else if (taskStatus === 'SUCCESS') {
    return (
      <div className="output-group">
        <p>Cover letter generated successfully!</p>
        <textarea ref={crewOutputRef} value={logs} readOnly />
      </div>
    );
  } else {
    return <div></div>;
  }
}

function App() {
  const [jobUrl, setJobUrl] = useState('https://www.workatastartup.com/jobs/66658');
  const [linkedinUrl, setLinkedinUrl] = useState('https://www.linkedin.com/in/seth-donaldson/');
  const [resumeFile, setResumeFile] = useState(null);
  const [logs, setLogs] = useState('');
  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const crewOutputRef = useRef(null);
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
    if (crewOutputRef.current) {
      crewOutputRef.current.scrollTop = crewOutputRef.current.scrollHeight;
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
    if (!jobUrl || !linkedinUrl || !resumeFile) {
      console.error('Missing required fields');
      // display popup/dialog
      toast.warn('Please fill out all fields before submitting the form.');
      return;
    }
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
      setLogs('');
      setTaskStatus('PENDING');
    } catch (error) {
      console.error('Error generating cover letter:', error);
    }
  };

  const handleDownloadOutputFile = async (fileName) => {
    try {
      const response = await axios.get(`https://localhost:5001/download/${sessionId}/${fileName}`);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      console.error('Error downloading output file:', error);
    }
  }

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
          setTaskStatus(state);
          console.log();
          if (state === 'SUCCESS' || state === 'FAILURE') {
            setTaskId(null);
          }
        } catch (error) {
          console.error('Error fetching task status:', error);
          setTaskId(null);
          setTaskStatus(null);
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
      <ToastContainer />
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
      <CrewOutput crewOutputRef={crewOutputRef} logs={logs} taskStatus={taskStatus} />
      <OutputFiles taskStatus={taskStatus} onClick={handleDownloadOutputFile} />
      <button onClick={handleCancelExecution}>Cancel Execution</button>
    </div>
  );
}

export default App;
