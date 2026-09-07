import React, { useState } from "react";
import {
  ArrowRight,
  BarChart3,
  Building2,
  Check,
  ChevronDown,
  Eye,
  EyeOff,
  Globe2,
  LockKeyhole,
  Mail,
  MapPin,
  Network,
  Ship,
  ShieldCheck,
  User,
  Users,
  X,
} from "lucide-react";

import "./Register.css";

function Register() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [form, setForm] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
    companyName: "",
    companyType: "",
    country: "",
    city: "",
    role: "",
    timezone: "Asia/Kolkata",
    terms: false,
  });

  const updateField = (field, value) => {
    setForm((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();

    if (form.password !== form.confirmPassword) {
      alert("Passwords do not match.");
      return;
    }

    if (!form.terms) {
      alert("Please accept the Terms of Service and Privacy Policy.");
      return;
    }

    console.log("Register form:", form);

    // Backend registration will be connected here.
  };

  const passwordRules = [
    {
      label: "At least 8 characters long",
      valid: form.password.length >= 8,
    },
    {
      label: "Include uppercase and lowercase letters",
      valid: /[a-z]/.test(form.password) && /[A-Z]/.test(form.password),
    },
    {
      label: "Include a number and a special character",
      valid: /\d/.test(form.password) && /[^A-Za-z0-9]/.test(form.password),
    },
  ];

  return (
    <div className="register-page">
      {/* LEFT BRAND PANEL */}
      <section className="register-brand-panel">
        <div className="register-image"></div>
        <div className="register-image-overlay"></div>

        <div className="register-brand-content">
          <div className="register-logo">
            <div className="register-logo-icon">
              <Ship size={31} strokeWidth={2.3} />
            </div>

            <div>
              <div className="register-logo-name">FREIGHTWISE</div>
              <div className="register-logo-tagline">
                Navigate Smarter. Charter Better.
              </div>
            </div>
          </div>

          <div className="register-brand-divider"></div>

          <div className="register-eyebrow">
            AI-POWERED FREIGHT INTELLIGENCE
          </div>

          <h1>
            Join a Smarter,
            <br />
            <span>More Connected</span>
            <br />
            <span>Shipping World.</span>
          </h1>

          <p className="register-brand-description">
            Create your account and get real-time insights,
            <br />
            AI-powered recommendations and smarter
            <br />
            chartering decisions with FreightWise.
          </p>

          <div className="register-features">
            <div className="register-feature">
              <div className="register-feature-icon">
                <BarChart3 size={22} />
              </div>

              <div>
                <strong>Real-time Market Insights</strong>
                <span>Make data-driven decisions.</span>
              </div>
            </div>

            <div className="register-feature">
              <div className="register-feature-icon">
                <Ship size={22} />
              </div>

              <div>
                <strong>Smarter Chartering</strong>
                <span>Find the best vessels and routes.</span>
              </div>
            </div>

            <div className="register-feature">
              <div className="register-feature-icon">
                <Network size={22} />
              </div>

              <div>
                <strong>Global Port Intelligence</strong>
                <span>Monitor port conditions and risks.</span>
              </div>
            </div>

            <div className="register-feature">
              <div className="register-feature-icon">
                <ShieldCheck size={22} />
              </div>

              <div>
                <strong>AI-Powered Forecasting</strong>
                <span>Plan with confidence.</span>
              </div>
            </div>
          </div>

          <div className="register-quote">
            <div className="register-quote-line"></div>

            <em>
              “Connecting Global Trade
              <br />
              for a Stronger Tomorrow.”
            </em>
          </div>

          <div className="register-stats">
            <div>
              <strong>150+</strong>
              <span>Ports Covered</span>
            </div>

            <div>
              <strong>10K+</strong>
              <span>Vessels Tracked</span>
            </div>

            <div>
              <strong>99.9%</strong>
              <span>Data Reliability</span>
            </div>
          </div>
        </div>
      </section>

      {/* RIGHT FORM PANEL */}
      <section className="register-form-panel">
        <div className="register-top-login">
          Already have an account?
          <a href="/login">Sign In</a>
        </div>

        <div className="register-form-shell">
          <div className="register-heading">
            <h2>Create Your FreightWise Account</h2>

            <p>
              Get started in minutes and unlock the power of AI-driven
              shipping intelligence.
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            {/* ACCOUNT INFORMATION */}
            <section className="register-section">
              <div className="register-section-heading">
                <div className="register-section-icon">
                  <User size={21} />
                </div>

                <div>
                  <h3>Account Information</h3>
                  <p>Tell us about yourself to get started.</p>
                </div>
              </div>

              <div className="register-grid">
                <div className="register-field">
                  <label>
                    Full Name <span>*</span>
                  </label>

                  <div className="register-input-wrap">
                    <User size={19} />

                    <input
                      type="text"
                      placeholder="Enter your full name"
                      value={form.fullName}
                      onChange={(e) =>
                        updateField("fullName", e.target.value)
                      }
                      required
                    />
                  </div>
                </div>

                <div className="register-field">
                  <label>
                    Email Address <span>*</span>
                  </label>

                  <div className="register-input-wrap">
                    <Mail size={19} />

                    <input
                      type="email"
                      placeholder="you@company.com"
                      value={form.email}
                      onChange={(e) => updateField("email", e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="register-field">
                  <label>
                    Password <span>*</span>
                  </label>

                  <div className="register-input-wrap">
                    <LockKeyhole size={19} />

                    <input
                      type={showPassword ? "text" : "password"}
                      placeholder="Create a strong password"
                      value={form.password}
                      onChange={(e) =>
                        updateField("password", e.target.value)
                      }
                      required
                    />

                    <button
                      type="button"
                      className="register-password-toggle"
                      onClick={() => setShowPassword(!showPassword)}
                      aria-label="Toggle password visibility"
                    >
                      {showPassword ? (
                        <EyeOff size={19} />
                      ) : (
                        <Eye size={19} />
                      )}
                    </button>
                  </div>
                </div>

                <div className="register-field">
                  <label>
                    Confirm Password <span>*</span>
                  </label>

                  <div className="register-input-wrap">
                    <LockKeyhole size={19} />

                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="Confirm your password"
                      value={form.confirmPassword}
                      onChange={(e) =>
                        updateField("confirmPassword", e.target.value)
                      }
                      required
                    />

                    <button
                      type="button"
                      className="register-password-toggle"
                      onClick={() =>
                        setShowConfirmPassword(!showConfirmPassword)
                      }
                      aria-label="Toggle confirm password visibility"
                    >
                      {showConfirmPassword ? (
                        <EyeOff size={19} />
                      ) : (
                        <Eye size={19} />
                      )}
                    </button>
                  </div>
                </div>
              </div>

              <div className="password-requirements">
                <div className="password-info-icon">
                  <ShieldCheck size={18} />
                </div>

                <div>
                  <strong>Password Requirements:</strong>

                  <ul>
                    {passwordRules.map((rule) => (
                      <li
                        key={rule.label}
                        className={rule.valid ? "valid" : ""}
                      >
                        <span className="password-rule-icon">
                          {rule.valid ? <Check size={12} /> : <X size={12} />}
                        </span>

                        {rule.label}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>

            {/* ORGANIZATION DETAILS */}
            <section className="register-section">
              <div className="register-section-heading">
                <div className="register-section-icon">
                  <Building2 size={21} />
                </div>

                <div>
                  <h3>Organization Details</h3>
                  <p>Help us understand your organization.</p>
                </div>
              </div>

              <div className="register-grid">
                <div className="register-field">
                  <label>
                    Company Name <span>*</span>
                  </label>

                  <div className="register-input-wrap">
                    <Building2 size={19} />

                    <input
                      type="text"
                      placeholder="Enter company name"
                      value={form.companyName}
                      onChange={(e) =>
                        updateField("companyName", e.target.value)
                      }
                      required
                    />
                  </div>
                </div>

                <div className="register-field">
                  <label>
                    Company Type <span>*</span>
                  </label>

                  <div className="register-input-wrap select-wrap">
                    <Building2 size={19} />

                    <select
                      value={form.companyType}
                      onChange={(e) =>
                        updateField("companyType", e.target.value)
                      }
                      required
                    >
                      <option value="">Select company type</option>
                      <option value="steel-producer">Steel Producer</option>
                      <option value="trader">Commodity Trader</option>
                      <option value="shipper">Shipper</option>
                      <option value="charterer">Charterer</option>
                      <option value="logistics">Logistics Provider</option>
                      <option value="other">Other</option>
                    </select>

                    <ChevronDown size={18} />
                  </div>
                </div>

                <div className="register-field">
                  <label>
                    Country <span>*</span>
                  </label>

                  <div className="register-input-wrap select-wrap">
                    <Globe2 size={19} />

                    <select
                      value={form.country}
                      onChange={(e) =>
                        updateField("country", e.target.value)
                      }
                      required
                    >
                      <option value="">Select country</option>
                      <option value="india">India</option>
                      <option value="australia">Australia</option>
                      <option value="indonesia">Indonesia</option>
                      <option value="south-africa">South Africa</option>
                      <option value="other">Other</option>
                    </select>

                    <ChevronDown size={18} />
                  </div>
                </div>

                <div className="register-field">
                  <label>
                    City <span>*</span>
                  </label>

                  <div className="register-input-wrap">
                    <MapPin size={19} />

                    <input
                      type="text"
                      placeholder="Enter city"
                      value={form.city}
                      onChange={(e) => updateField("city", e.target.value)}
                      required
                    />
                  </div>
                </div>
              </div>
            </section>

            {/* PREFERENCES */}
            <section className="register-section">
              <div className="register-section-heading">
                <div className="register-section-icon">
                  <Users size={21} />
                </div>

                <div>
                  <h3>Preferences</h3>
                  <p>Set your preferences for a better experience.</p>
                </div>
              </div>

              <div className="register-grid">
                <div className="register-field">
                  <label>
                    Default Role <span>*</span>
                  </label>

                  <div className="register-input-wrap select-wrap">
                    <User size={19} />

                    <select
                      value={form.role}
                      onChange={(e) => updateField("role", e.target.value)}
                      required
                    >
                      <option value="">Select role</option>
                      <option value="charterer">Charterer</option>
                      <option value="procurement">Procurement Manager</option>
                      <option value="logistics">Logistics Manager</option>
                      <option value="analyst">Freight Analyst</option>
                      <option value="operations">Operations Manager</option>
                    </select>

                    <ChevronDown size={18} />
                  </div>
                </div>

                <div className="register-field">
                  <label>
                    Time Zone <span>*</span>
                  </label>

                  <div className="register-input-wrap select-wrap">
                    <Globe2 size={19} />

                    <select
                      value={form.timezone}
                      onChange={(e) =>
                        updateField("timezone", e.target.value)
                      }
                      required
                    >
                      <option value="Asia/Kolkata">
                        (GMT+05:30) Asia/Kolkata
                      </option>
                      <option value="Asia/Singapore">
                        (GMT+08:00) Asia/Singapore
                      </option>
                      <option value="Australia/Sydney">
                        (GMT+10:00) Australia/Sydney
                      </option>
                      <option value="UTC">(GMT+00:00) UTC</option>
                    </select>

                    <ChevronDown size={18} />
                  </div>
                </div>
              </div>
            </section>

            {/* TERMS */}
            <label className="register-terms">
              <input
                type="checkbox"
                checked={form.terms}
                onChange={(e) => updateField("terms", e.target.checked)}
              />

              <span className="custom-checkbox">
                {form.terms && <Check size={13} />}
              </span>

              <span>
                I agree to the{" "}
                <a href="/terms" onClick={(e) => e.preventDefault()}>
                  Terms of Service
                </a>{" "}
                and{" "}
                <a href="/privacy" onClick={(e) => e.preventDefault()}>
                  Privacy Policy
                </a>
                <b> *</b>
              </span>
            </label>

            <button type="submit" className="register-submit">
              Create Account
              <ArrowRight size={19} />
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}

export default Register;