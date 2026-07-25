import api from "./axios";

export const authApi = {
  register: (payload) => {
    const form = new FormData();
    form.append("last_name", payload.last_name);
    form.append("first_name", payload.first_name);
    form.append("patronymic", payload.patronymic || "");
    form.append("email", payload.email);
    form.append("username", payload.username);
    form.append("password", payload.password);
    form.append("password_confirm", payload.password_confirm);
    form.append("academic_degree", payload.academic_degree || "none");
    form.append("academic_title", payload.academic_title || "none");
    form.append("position", payload.position || "");
    form.append("department", payload.department);
    form.append("research_interests", payload.research_interests || "");
    if (payload.photo) form.append("photo", payload.photo);
    return api.post("/auth/register/", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  verifyEmail: (email, code) => api.post("/auth/verify-email/", { email, code }),
  resendCode: (email) => api.post("/auth/resend-code/", { email }),
  login: (login, password) => api.post("/auth/login/", { login, password }),
  me: () => api.get("/me/"),
};

export const departmentsApi = {
  list: () => api.get("/departments/"),
};

export const specialistsApi = {
  search: ({ name, department, page }) =>
    api.get("/specialists/", { params: { name, department, page } }),
  detail: (id) => api.get(`/specialists/${id}/`),
  me: () => api.get("/specialists/me/"),
  updateMe: (payload, { isMultipart = false } = {}) => {
    if (!isMultipart) {
      return api.patch("/specialists/me/", payload);
    }
    const form = new FormData();
    Object.entries(payload).forEach(([key, value]) => {
      if (value !== undefined && value !== null) form.append(key, value);
    });
    return api.patch("/specialists/me/", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

function buildWorkFormData(payload) {
  const form = new FormData();
  Object.entries(payload).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    if (key === "confirm_duplicate") {
      form.append(key, value ? "true" : "false");
      return;
    }
    form.append(key, value);
  });
  return form;
}

export const worksApi = {
  listMine: ({ category, page, ordering, search } = {}) =>
    api.get("/specialists/me/works/", { params: { category, page, ordering, search } }),
  listPublic: (specialistId, { category, page, ordering } = {}) =>
    api.get(`/specialists/${specialistId}/works/`, { params: { category, page, ordering } }),
  create: (payload) =>
    api.post("/specialists/me/works/", buildWorkFormData(payload), {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  update: (id, payload) =>
    api.patch(`/specialists/me/works/${id}/`, buildWorkFormData(payload), {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  delete: (id) => api.delete(`/specialists/me/works/${id}/`),
};

export const ACADEMIC_DEGREES = [
  { value: "none", label: "Yo'q" },
  { value: "bachelor", label: "Bakalavr" },
  { value: "master", label: "Magistr" },
  { value: "phd", label: "PhD" },
  { value: "dsc", label: "DSc" },
  { value: "candidate_legacy", label: "Fan nomzodi" },
  { value: "doctor_legacy", label: "Fan doktori" },
];

export const ACADEMIC_TITLES = [
  { value: "none", label: "Yo'q" },
  { value: "senior_researcher", label: "Katta ilmiy xodim" },
  { value: "docent", label: "Dotsent" },
  { value: "professor", label: "Professor" },
  { value: "academician", label: "Akademik" },
];

export const POSITIONS = [
  { value: "junior_researcher", label: "Kichik ilmiy xodim" },
  { value: "senior_researcher", label: "Katta ilmiy xodim" },
  { value: "leading_researcher", label: "Yetakchi ilmiy xodim" },
  { value: "chief_researcher", label: "Bosh ilmiy xodim" },
  { value: "lab_head", label: "Laboratoriya mudiri" },
  { value: "department_head", label: "Bo'lim boshlig'i" },
];

// Tab order matters -- matches the spec exactly.
// Tab order follows the official report structure (II-VI).
export const WORK_CATEGORIES = [
  { value: "foreign_article", tabLabel: "Xorijiy maqolalar", singularLabel: "Xorijiy maqola" },
  { value: "local_article", tabLabel: "Mahalliy maqolalar", singularLabel: "Mahalliy maqola" },
  { value: "thesis", tabLabel: "Tezislar", singularLabel: "Tezis" },
  { value: "conference_participation", tabLabel: "Anjumanda ishtirok", singularLabel: "Anjumanda ishtirok" },
  { value: "patent", tabLabel: "Patentlar", singularLabel: "Patent" },
  { value: "other_publication", tabLabel: "Boshqa nashrlar", singularLabel: "Boshqa nashr" },
];

export const AUTHORSHIP_OPTIONS = [
  { value: "main_author", label: "Asosiy muallif" },
  { value: "co_author", label: "Hammuallif" },
];

export const JOURNAL_SCOPE_OPTIONS = [
  { value: "scopus_wos", label: "Scopus va/yoki Web of Science bazasiga kiritilgan" },
  { value: "other_foreign", label: "Boshqa xorijiy jurnal" },
  { value: "cis", label: "MDH jurnali" },
  { value: "local", label: "Mahalliy jurnal" },
];

export const INDEXED_IN_OPTIONS = [
  { value: "scopus", label: "Scopus" },
  { value: "wos", label: "Web of Science" },
  { value: "both", label: "Scopus va Web of Science" },
];

export const QUARTILE_OPTIONS = [
  { value: "Q1", label: "Q1" },
  { value: "Q2", label: "Q2" },
  { value: "Q3", label: "Q3" },
  { value: "Q4", label: "Q4" },
];

export const CONFERENCE_SCOPE_OPTIONS = [
  { value: "scopus_wos", label: "Scopus/WoS to'plami" },
  { value: "other_foreign", label: "Boshqa xorijiy anjuman" },
  { value: "cis", label: "MDH anjumani" },
  { value: "local", label: "Mahalliy anjuman" },
];

export const LOCAL_CONF_LEVEL_OPTIONS = [
  { value: "international", label: "Xalqaro anjuman" },
  { value: "republic", label: "Respublika anjumani" },
];

export const PRESENTATION_TYPE_OPTIONS = [
  { value: "oral", label: "Og'zaki" },
  { value: "plenary", label: "Plenar" },
];

export const PARTICIPATION_SCOPE_OPTIONS = [
  { value: "foreign", label: "Xorijiy" },
  { value: "republic", label: "Respublika" },
];

export const PUBLICATION_TYPE_OPTIONS = [
  { value: "monograph", label: "Monografiya" },
  { value: "textbook", label: "Darslik" },
  { value: "manual", label: "O'quv qo'llanma" },
];

export const PATENT_CATEGORY_OPTIONS = [
  { value: "invention", label: "Ixtiro (patent)" },
  { value: "foreign_patent", label: "Xorijiy patent" },
  { value: "utility_model", label: "Foydali modelga patent" },
  { value: "patent_application", label: "Patent uchun talabnoma" },
  { value: "trademark", label: "Tovar belgisi" },
  { value: "software_certificate", label: "Dasturiy mahsulot guvohnomasi" },
  { value: "license_agreement", label: "Litsenziya shartnomasi" },
];

export const reportsApi = {
  me: ({ year, date_from, date_to } = {}) =>
    api.get("/reports/me/", { params: { year, date_from, date_to } }),
  drilldown: (code, year) => api.get("/reports/me/drilldown/", { params: { code, year } }),
  exportMe: ({ year } = {}) =>
    api.get("/reports/me/export/", { params: { year }, responseType: "blob" }),
  institute: ({ year, department, employee } = {}) =>
    api.get("/reports/institute/", { params: { year, department, employee } }),
  exportInstitute: ({ year, department } = {}) =>
    api.get("/reports/institute/export/", { params: { year, department }, responseType: "blob" }),
};

export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export function flattenApiErrors(data) {
  if (!data || typeof data !== "object") return { fieldErrors: {}, generic: null };
  const fieldErrors = {};
  let generic = null;
  Object.entries(data).forEach(([key, value]) => {
    const message = Array.isArray(value) ? String(value[0]) : String(value);
    if (key === "detail" || key === "non_field_errors") {
      generic = message;
    } else {
      fieldErrors[key] = message;
    }
  });
  return { fieldErrors, generic };
}

export function errorCode(data) {
  if (!data?.code) return null;
  return Array.isArray(data.code) ? String(data.code[0]) : String(data.code);
}
