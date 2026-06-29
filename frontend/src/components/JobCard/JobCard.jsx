import "./JobCard.css";

function JobCard({ job }) {
  return (
    <div className="job-card">
      <div className="job-header">
        <h3>{job.title}</h3>
        <span>{job.company}</span>
      </div>

      <p className="location">{job.location || "Location not specified"}</p>
      <p className="source">Source: {job.source}</p>

      <a href={job.link} target="_blank" rel="noreferrer">
        View Job →
      </a>
    </div>
  );
}

export default JobCard;
