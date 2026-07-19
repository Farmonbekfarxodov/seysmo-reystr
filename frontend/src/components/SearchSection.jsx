import React, { useEffect, useState } from "react";

import { specialistsApi } from "../api/endpoints";
import { useDebounce } from "../hooks/useDebounce.js";
import SearchBar from "./SearchBar.jsx";
import SpecialistList from "./SpecialistList.jsx";

export default function SearchSection() {
  const [name, setName] = useState("");
  const [direction, setDirection] = useState("");
  const [page, setPage] = useState(1);

  const debouncedName = useDebounce(name, 400);
  const debouncedDirection = useDebounce(direction, 400);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [results, setResults] = useState([]);
  const [count, setCount] = useState(0);
  const [numPages, setNumPages] = useState(1);

  // Reset to page 1 whenever the (debounced) search terms change.
  useEffect(() => {
    setPage(1);
  }, [debouncedName, debouncedDirection]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    specialistsApi
      .search({ name: debouncedName, direction: debouncedDirection, page })
      .then((res) => {
        if (cancelled) return;
        setResults(res.data.results);
        setCount(res.data.count);
        setNumPages(res.data.num_pages || 1);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(
          err.response?.status === 401
            ? "Log in to search the registry."
            : "Something went wrong while searching. Please try again."
        );
        setResults([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [debouncedName, debouncedDirection, page]);

  return (
    <div>
      <h2>Search specialists</h2>
      <SearchBar
        name={name}
        direction={direction}
        onNameChange={setName}
        onDirectionChange={setDirection}
      />

      {error ? (
        <div className="alert alert-error">{error}</div>
      ) : (
        <>
          {!loading && <div className="search-meta">{count} specialist(s) found</div>}
          <SpecialistList
            loading={loading}
            results={results}
            page={page}
            numPages={numPages}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
