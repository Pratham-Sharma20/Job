import JobCard from "../JobCard/JobCard";
import "./JobList.css";

function JobList({ jobs, loading }) {
  if (loading) {
    return <p className="status">Loading jobs...</p>;
  }

  if (jobs.length === 0) {
    return <p className="status">No jobs found.</p>;
  }

  return (
    <section className="jobs-grid">
      {jobs.map((job, index) => (
        <JobCard key={job._id || index} job={job} />
      ))}
    </section>
  );
}

export default JobList;
