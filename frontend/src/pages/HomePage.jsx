import React, { useEffect, useState } from "react";

import { departmentsApi, specialistsApi } from "../api/endpoints";
import SearchBar from "../components/SearchBar.jsx";
import Seismogram from "../components/Seismogram.jsx";
import SpecialistList from "../components/SpecialistList.jsx";
import { useDebounce } from "../hooks/useDebounce.js";
import uz from "../i18n/uz.js";

export default function HomePage() {
  const [departments, setDepartments] = useState([]);
  const [name, setName] = useState("");
  const [department, setDepartment] = useState("");
  const [page, setPage] = useState(1);

  const debouncedName = useDebounce(name, 400);

  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState([]);
  const [count, setCount] = useState(0);
  const [numPages, setNumPages] = useState(1);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    departmentsApi.list().then((res) => setDepartments(res.data)).catch(() => setDepartments([]));
  }, []);

  useEffect(() => {
    setPage(1);
  }, [debouncedName, department]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    specialistsApi
      .search({ name: debouncedName, department, page })
      .then((res) => {
        if (cancelled) return;
        setResults(res.data.results);
        setCount(res.data.count);
        setNumPages(res.data.num_pages || 1);
        setHasSearched(true);
      })
      .catch(() => {
        if (!cancelled) setResults([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [debouncedName, department, page]);

  return (
    <div className="flex flex-1 flex-col items-center px-5 pb-20 pt-14 sm:pt-20">
      <h1 className="max-w-2xl text-center text-4xl font-semibold leading-tight text-ink sm:text-5xl">
        {uz.common.instituteName}
        <span className="block text-2xl font-normal text-ink-soft sm:text-3xl">{uz.common.registryName}</span>
      </h1>

      <Seismogram className="mt-6 h-10 w-full max-w-md text-sand" />

      <div className="mt-8 flex w-full justify-center">
        <SearchBar
          name={name}
          department={department}
          departments={departments}
          onNameChange={setName}
          onDepartmentChange={setDepartment}
        />
      </div>

      <div className="mt-10 w-full max-w-5xl">
        {hasSearched && !loading && (
          <p className="mb-4 text-sm text-ink-faint">{uz.search.resultsCount(count)}</p>
        )}
        <SpecialistList
          loading={loading}
          results={results}
          page={page}
          numPages={numPages}
          onPageChange={setPage}
        />
      </div>
    </div>
  );
}
