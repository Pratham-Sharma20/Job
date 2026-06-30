import "./Sidebar.css";

function Sidebar({ companies = [], selectedCompanies = [], setSelectedCompanies }) {
  const handleCheckboxChange = (company) => {
    if (selectedCompanies.includes(company)) {
      setSelectedCompanies(selectedCompanies.filter((c) => c !== company));
    } else {
      setSelectedCompanies([...selectedCompanies, company]);
    }
  };

  return (
    <aside className="sidebar">
      <h2>JobBoard</h2>
      <p>Early career & internship tracker</p>

      {companies.length > 0 && (
        <div className="filter-section">
          <h3>Filter by Company</h3>
          <div className="checkbox-list">
            {companies.map((company) => (
              <label key={company} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selectedCompanies.includes(company)}
                  onChange={() => handleCheckboxChange(company)}
                />
                <span className="checkbox-text">{company}</span>
              </label>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
}

export default Sidebar;
