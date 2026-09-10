import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  Bell,
  ChevronDown,
  User,
  Mail,
  Building2,
  BriefcaseBusiness,
  Phone,
  Save,
  X,
  LayoutDashboard,
  PlusCircle,
  BarChart3,
  Ship,
  Anchor,
  RotateCcw,
  Settings as SettingsIcon,
} from "lucide-react";

import "./Profile.css";


const mainNavigation = [
  {
    label: "Dashboard",
    path: "/",
    icon: LayoutDashboard,
  },
  {
    label: "New Voyage",
    path: "/new-voyage",
    icon: PlusCircle,
  },
  {
    label: "Analysis",
    path: "/analysis",
    icon: BarChart3,
  },
  {
    label: "Vessels",
    path: "/vessels",
    icon: Ship,
  },
  {
    label: "Ports",
    path: "/ports",
    icon: Anchor,
  },
  {
    label: "Simulation",
    path: "/simulation",
    icon: RotateCcw,
  },
  {
    label: "Settings",
    path: "/settings",
    icon: SettingsIcon,
  },
];


function Profile() {
  const [profile, setProfile] = useState({
    fullName: "",
    email: "",
    organization: "",
    role: "",
    phone: "",
  });


  const [saved, setSaved] = useState(false);


  const updateProfile = (field, value) => {
    setProfile((previous) => ({
      ...previous,
      [field]: value,
    }));

    setSaved(false);
  };


  const handleSave = () => {
    console.log("Profile saved:", profile);
    setSaved(true);
  };


  const handleCancel = () => {
    setProfile({
      fullName: "",
      email: "",
      organization: "",
      role: "",
      phone: "",
    });

    setSaved(false);
  };


  return (
    <div className="profile-page">

      {/* =========================
          SIDEBAR
      ========================= */}

      <aside className="profile-sidebar">

        <div className="profile-brand">

          <div className="profile-brand-logo">
            <Ship size={35} strokeWidth={1.6} />
          </div>

          <h1>FREIGHTWISE</h1>

          <p>
            Navigate Smarter.
            <br />
            Charter Better.
          </p>

        </div>


        <nav className="profile-main-navigation">

          {mainNavigation.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.label}
                type="button"
                onClick={() => navigate(item.path)}
                className="profile-main-nav-item"
              >
                <Icon size={19} strokeWidth={1.8} />

                <span>
                  {item.label}
                </span>
              </button>
            );
          })}

        </nav>


        <div className="profile-sidebar-bottom">

          <div className="profile-ai-status">

            <div className="profile-ai-header">

              <span className="profile-online-dot"></span>

              <span>
                AI Engine Online
              </span>

            </div>

            <p>
              Intelligence systems operational
            </p>

          </div>


          <div className="profile-sidebar-wave"></div>


          <div className="profile-sidebar-quote">
            “Right Data.
            <br />
            Smarter Decisions.
            <br />
            Greener Seas.”
          </div>

        </div>

      </aside>


      {/* =========================
          MAIN
      ========================= */}

      <main className="profile-main">


        {/* =========================
            TOPBAR
        ========================= */}

        <header className="profile-topbar">

          <div className="profile-search">

            <Search size={19} />

            <input
              type="text"
              placeholder="Search ports, vessels, routes..."
            />

          </div>


          <div className="profile-topbar-actions">

            <button
              type="button"
              className="profile-notification-button"
              aria-label="Notifications"
              onClick={() => navigate("/notifications")}
            >

              <Bell size={21} />

              <span className="profile-notification-count">
                3
              </span>

            </button>


            <div className="profile-topbar-divider"></div>


            <div className="profile-user-menu">

              <div className="profile-user-avatar">
                U
              </div>

              <span>
                User
              </span>

              <ChevronDown size={16} />

            </div>

          </div>

        </header>


        {/* =========================
            PAGE HEADER
        ========================= */}

        <section className="profile-page-header">

          <div>

            <div className="profile-kicker">
              ACCOUNT
            </div>

            <h2>
              User Profile
            </h2>

            <p>
              Manage your personal and organizational information
            </p>

          </div>


          <div className="profile-header-icon">
            <User size={72} strokeWidth={1.2} />
          </div>

        </section>


        {/* =========================
            CONTENT
        ========================= */}

        <section className="profile-content">


          {/* PROFILE CARD */}

          <div className="profile-card">

            <div className="profile-card-heading">

              <div className="profile-card-heading-icon">
                <User size={28} />
              </div>

              <div>

                <h2>
                  Profile Information
                </h2>

                <p>
                  Update your personal and organizational details
                </p>

              </div>

            </div>


            <div className="profile-form">


              {/* FULL NAME */}

              <div className="profile-field">

                <label>
                  Full Name
                  <span>*</span>
                </label>

                <div className="profile-input-wrapper">

                  <User size={18} />

                  <input
                    type="text"
                    value={profile.fullName}
                    onChange={(event) =>
                      updateProfile(
                        "fullName",
                        event.target.value
                      )
                    }
                    placeholder="Enter your full name"
                  />

                </div>

              </div>


              {/* EMAIL */}

              <div className="profile-field">

                <label>
                  Email
                  <span>*</span>
                </label>

                <div className="profile-input-wrapper">

                  <Mail size={18} />

                  <input
                    type="email"
                    value={profile.email}
                    onChange={(event) =>
                      updateProfile(
                        "email",
                        event.target.value
                      )
                    }
                    placeholder="Enter your email address"
                  />

                </div>

              </div>


              {/* ORGANIZATION */}

              <div className="profile-field">

                <label>
                  Organization
                  <span>*</span>
                </label>

                <div className="profile-input-wrapper">

                  <Building2 size={18} />

                  <input
                    type="text"
                    value={profile.organization}
                    onChange={(event) =>
                      updateProfile(
                        "organization",
                        event.target.value
                      )
                    }
                    placeholder="Enter organization name"
                  />

                </div>

              </div>


              {/* ROLE */}

              <div className="profile-field">

                <label>
                  Role
                  <span>*</span>
                </label>

                <div className="profile-input-wrapper">

                  <BriefcaseBusiness size={18} />

                  <select
                    value={profile.role}
                    onChange={(event) =>
                      updateProfile(
                        "role",
                        event.target.value
                      )
                    }
                  >

                    <option value="">
                      Select your role
                    </option>

                    <option>
                      Procurement Manager
                    </option>

                    <option>
                      Chartering Manager
                    </option>

                    <option>
                      Logistics Manager
                    </option>

                    <option>
                      Operations Manager
                    </option>

                    <option>
                      Analyst
                    </option>

                  </select>

                </div>

              </div>


              {/* PHONE */}

              <div className="profile-field">

                <label>
                  Phone Number
                </label>

                <div className="profile-input-wrapper">

                  <Phone size={18} />

                  <input
                    type="tel"
                    value={profile.phone}
                    onChange={(event) =>
                      updateProfile(
                        "phone",
                        event.target.value
                      )
                    }
                    placeholder="Enter phone number"
                  />

                </div>

              </div>

            </div>


            {/* ACTIONS */}

            <div className="profile-actions">

              <button
                type="button"
                className="profile-cancel-button"
                onClick={handleCancel}
              >
                <X size={17} />
                Cancel
              </button>


              <button
                type="button"
                className="profile-save-button"
                onClick={handleSave}
              >
                <Save size={17} />
                Save Changes
              </button>

            </div>


            {saved && (
              <div className="profile-save-message">
                Profile changes saved successfully.
              </div>
            )}

          </div>


          {/* ACCOUNT SUMMARY */}

          <div className="profile-account-card">

            <div className="profile-account-avatar">
              <User size={38} />
            </div>

            <h3>
              User Account
            </h3>

            <p>
              FreightWise workspace member
            </p>


            <div className="profile-account-divider"></div>


            <div className="profile-account-item">
              <span>
                Account Status
              </span>

              <strong>
                Active
              </strong>
            </div>


            <div className="profile-account-item">
              <span>
                AI Engine
              </span>

              <strong>
                Online
              </strong>
            </div>


            <div className="profile-account-item">
              <span>
                Workspace
              </span>

              <strong>
                East Coast India
              </strong>
            </div>

          </div>

        </section>


        {/* FOOTER */}

        <footer className="profile-footer">

          <span>
            © 2026 FreightWise. All rights reserved.
          </span>

          <div>

            <a href="#help">
              Help
            </a>

            <a href="#privacy">
              Privacy
            </a>

            <a href="#terms">
              Terms
            </a>

            <a href="#contact">
              Contact
            </a>

          </div>

        </footer>

      </main>

    </div>
  );
}


export default Profile;