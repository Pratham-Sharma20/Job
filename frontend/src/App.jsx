import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar/Sidebar";
import Hero from "./components/Hero/Hero";
import JobList from "./components/JobList/JobList";
import Pagination from "./components/Pagination/Pagination";
import "./App.css";

function App() {
  const [jobs, setJobs] = useState([]);
  const [search, setSearch] = useState("");
  const [selectedCompanies, setSelectedCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const jobsPerPage = 12;

  useEffect(() => {
    const backendUrl = import.meta.env.VITE_BACKEND_URL || "http://localhost:5000";
    fetch(`${backendUrl}/jobs`)
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setJobs(data);
        } else {
          console.error("Expected an array but got:", data);
          setJobs([]);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error fetching jobs:", err);
        setLoading(false);
      });
  }, []);

  // Reset to first page when search or filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [search, selectedCompanies]);

  const uniqueCompanies = Array.from(new Set(jobs.map((job) => job.company))).sort();

  const filteredJobs = jobs.filter((job) => {
    // Check company filter
    if (selectedCompanies.length > 0 && !selectedCompanies.includes(job.company)) {
      return false;
    }
    
    // Check text search
    const text = `${job.company} ${job.title} ${job.location} ${job.source}`.toLowerCase();
    return text.includes(search.toLowerCase());
  });

  // Calculate pagination data
  const totalPages = Math.ceil(filteredJobs.length / jobsPerPage);
  const indexOfLastJob = currentPage * jobsPerPage;
  const indexOfFirstJob = indexOfLastJob - jobsPerPage;
  const currentJobs = filteredJobs.slice(indexOfFirstJob, indexOfLastJob);

  return (
    <div className="app">
      <Sidebar 
        companies={uniqueCompanies} 
        selectedCompanies={selectedCompanies} 
        setSelectedCompanies={setSelectedCompanies} 
      />
      <main className="main">
        <Hero search={search} setSearch={setSearch} />
        <JobList jobs={currentJobs} loading={loading} />
        
        {!loading && filteredJobs.length > 0 && (
          <Pagination 
            currentPage={currentPage} 
            totalPages={totalPages} 
            onPageChange={setCurrentPage} 
          />
        )}
      </main>
    </div>
  );
}

export default App;