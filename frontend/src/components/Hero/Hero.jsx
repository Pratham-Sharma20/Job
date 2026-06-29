import "./Hero.css";

function Hero({ search, setSearch }) {
  return (
    <section className="hero">
      <h1>Early Career Jobs</h1>
      <p>Browse internships, new grad, fresher and SDE-I roles.</p>

      <div className="search-container">
        <input
          type="text"
          placeholder="Search by company, role, location..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        {search && (
          <button 
            className="clear-btn" 
            onClick={() => setSearch("")} 
            aria-label="Clear search"
          >
            &times;
          </button>
        )}
      </div>
    </section>
  );
}

export default Hero;
