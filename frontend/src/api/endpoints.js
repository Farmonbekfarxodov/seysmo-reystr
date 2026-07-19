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
    (payload.documents || []).forEach((file) => form.append("documents", file));
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
  uploadDocument: (file) => {
    const form = new FormData();
    form.append("file", file);
    return api.post("/specialists/me/documents/", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  deleteDocument: (id) => api.delete(`/specialists/me/documents/${id}/`),
};

export const ACADEMIC_DEGREES = [
  { value: "none", label: "Yo'q" },
  { value: "bsc", label: "Bakalavr" },
  { value: "msc", label: "Magistr" },
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

/** DRF wraps validate()-raised dict errors so every leaf is an array.
 * This pulls out a flat { field: "message" } map plus a top-level string. */
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
