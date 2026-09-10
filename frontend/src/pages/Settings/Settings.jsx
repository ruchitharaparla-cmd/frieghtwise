import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  Bell,
  ChevronDown,
  LayoutDashboard,
  PlusCircle,
  BarChart3,
  Ship,
  Anchor,
  RotateCcw,
  Settings as SettingsIcon,
  User,
  BellRing,
  LineChart,
  Compass,
  ShieldCheck,
  Palette,
  Database,
  Save,
  X,
  Mail,
  Smartphone,
  AlertTriangle,
  CloudRain,
  TrendingUp,
  CalendarDays,
  Gauge,
  Globe2,
  Box,
  Ruler,
  Moon,
  Sun,
  Monitor,
  SlidersHorizontal,
  Lock,
  Download,
  Trash2,
  KeyRound,
  Server,
  Activity,
  CheckCircle2,
} from "lucide-react";

import "./Settings.css";


/* =========================================================
   MAIN SIDEBAR NAVIGATION
========================================================= */

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


/* =========================================================
   SETTINGS SIDEBAR
========================================================= */

const settingsNavigation = [
  {
    label: "Profile",
    icon: User,
  },
  {
    label: "Notifications",
    icon: BellRing,
  },
  {
    label: "Forecasting Preferences",
    icon: LineChart,
  },
  {
    label: "Default Voyage Settings",
    icon: Compass,
  },
  {
    label: "Data & Privacy",
    icon: ShieldCheck,
  },
  {
    label: "Appearance",
    icon: Palette,
  },
  {
    label: "System & API",
    icon: Database,
  },
];


/* =========================================================
   SETTINGS COMPONENT
========================================================= */

const Settings = () => {
  const [activeSection, setActiveSection] = useState("Profile");

  const [profile, setProfile] = useState({
    fullName: "",
    email: "",
    organization: "",
    role: "",
    phone: "",
  });

  const [notifications, setNotifications] = useState({
    freightRate: true,
    charterWindow: true,
    portCongestion: true,
    weatherRisk: true,
    marketDigest: false,
    modelUpdates: false,
  });

  const [forecasting, setForecasting] = useState({
    horizon: "30",
    frequency: "Daily",
    benchmark: "",
    confidence: "70",
    region: "",
  });

  const [voyageDefaults, setVoyageDefaults] = useState({
    cargo: "",
    origin: "",
    destination: "East Coast India",
    vesselClass: "",
    arrivalBuffer: "2",
    units: "Metric",
    currency: "USD",
  });

  const [privacy, setPrivacy] = useState({
    analytics: true,
    activityHistory: true,
    dataRetention: "12 months",
  });

  const [appearance, setAppearance] = useState({
    theme: "System",
    density: "Comfortable",
    startPage: "Dashboard",
    charts: "Detailed",
  });


  /* =======================================================
     GENERIC CHANGE HANDLERS
  ======================================================= */

  const updateProfile = (field, value) => {
    setProfile((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const updateForecasting = (field, value) => {
    setForecasting((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const updateVoyageDefaults = (field, value) => {
    setVoyageDefaults((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const updatePrivacy = (field, value) => {
    setPrivacy((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const updateAppearance = (field, value) => {
    setAppearance((previous) => ({
      ...previous,
      [field]: value,
    }));
  };


  const toggleNotification = (field) => {
    setNotifications((previous) => ({
      ...previous,
      [field]: !previous[field],
    }));
  };


  const handleProfileCancel = () => {
    setProfile({
      fullName: "",
      email: "",
      organization: "",
      role: "",
      phone: "",
    });
  };


  const handleSave = () => {
    /*
      Backend persistence will be connected later.
      Keep this handler ready for the API integration.
    */

    console.log("FreightWise settings saved");
  };


  return (
    <div className="settings-page">


      {/* =====================================================
          LEFT SIDEBAR
      ===================================================== */}

      <aside className="settings-sidebar">


        {/* BRAND */}

        <div className="sidebar-brand">

          <div className="sidebar-brand-logo">
            <Ship
              size={35}
              strokeWidth={1.6}
            />
          </div>

          <h1>FREIGHTWISE</h1>

          <p>
            Navigate Smarter.
            <br />
            Charter Better.
          </p>

        </div>


        {/* MAIN NAVIGATION */}

        <nav className="main-navigation">

          {mainNavigation.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.label}
                type="button"
                onClick={() => navigate(item.path)}
                className={`main-nav-item ${
                  item.label === "Settings"
                    ? "active"
                    : ""
                }`}
              >

                <Icon
                  size={19}
                  strokeWidth={1.8}
                />

                <span>
                  {item.label}
                </span>

              </button>
            );
          })}

        </nav>


        {/* SIDEBAR BOTTOM */}

        <div className="sidebar-bottom">

          <div className="ai-status-card">

            <div className="ai-status-header">

              <span className="online-dot"></span>

              <span>
                AI Engine Online
              </span>

            </div>

            <p>
              Intelligence systems operational
            </p>

          </div>


          <div className="sidebar-wave"></div>


          <div className="sidebar-quote">
            “Right Data.
            <br />
            Smarter Decisions.
            <br />
            Greener Seas.”
          </div>

        </div>

      </aside>



      {/* =====================================================
          MAIN CONTENT
      ===================================================== */}

      <main className="settings-main">


        {/* ===================================================
            TOPBAR
        =================================================== */}

        <header className="settings-topbar">

          <div className="settings-search">

            <Search size={19} />

            <input
              type="text"
              placeholder="Search ports, vessels, routes..."
            />

          </div>


          <div className="topbar-actions">

            <button
              type="button"
              className="notification-button"
              aria-label="Notifications"
              onClick={() => navigate("/notifications")}
            >

              <Bell size={21} />

              <span className="notification-count">
                3
              </span>

            </button>


            <div className="topbar-divider"></div>


            <button
              type="button"
              className="user-menu"
              onClick={() => navigate("/profile")}
            >

              <div className="user-avatar">
                U
              </div>

              <span>
                User
              </span>

              <ChevronDown size={16} />

            </button>

          </div>

        </header>



        {/* ===================================================
            HERO
        =================================================== */}

        <section className="settings-hero">

          <div className="settings-hero-content">

            <div className="settings-kicker">
              SYSTEM CONFIGURATION
            </div>

            <h2>
              Settings
            </h2>

            <p>
              Manage your FreightWise preferences, account
              and system configuration
            </p>

          </div>


          <div className="hero-ship-image"></div>


          <div className="hero-message">

            <span>
              “Smarter Settings.
            </span>

            <span>
              A Stronger Voyage.”
            </span>

            <i></i>

          </div>

        </section>



        {/* ===================================================
            SETTINGS WORKSPACE
        =================================================== */}

        <section className="settings-body">


          {/* =================================================
              SETTINGS MENU
          ================================================= */}

          <aside className="settings-menu">

            {settingsNavigation.map((item) => {

              const Icon = item.icon;

              return (
                <button
                  key={item.label}
                  type="button"
                  className={`settings-menu-item ${
                    activeSection === item.label
                      ? "active"
                      : ""
                  }`}
                  onClick={() =>
                    setActiveSection(item.label)
                  }
                >

                  <Icon
                    size={21}
                    strokeWidth={1.8}
                  />

                  <span>
                    {item.label}
                  </span>

                </button>
              );

            })}

          </aside>



          {/* =================================================
              RIGHT CONTENT
          ================================================= */}

          <div className="settings-panel">


            {activeSection === "Profile" && (

              <ProfileSection
                profile={profile}
                updateProfile={updateProfile}
                onCancel={handleProfileCancel}
                onSave={handleSave}
              />

            )}


            {activeSection === "Notifications" && (

              <NotificationsSection
                notifications={notifications}
                toggleNotification={toggleNotification}
                onSave={handleSave}
              />

            )}


            {activeSection === "Forecasting Preferences" && (

              <ForecastingSection
                forecasting={forecasting}
                updateForecasting={updateForecasting}
                onSave={handleSave}
              />

            )}


            {activeSection === "Default Voyage Settings" && (

              <VoyageDefaultsSection
                values={voyageDefaults}
                updateValue={updateVoyageDefaults}
                onSave={handleSave}
              />

            )}


            {activeSection === "Data & Privacy" && (

              <PrivacySection
                privacy={privacy}
                updatePrivacy={updatePrivacy}
                onSave={handleSave}
              />

            )}


            {activeSection === "Appearance" && (

              <AppearanceSection
                appearance={appearance}
                updateAppearance={updateAppearance}
                onSave={handleSave}
              />

            )}


            {activeSection === "System & API" && (

              <SystemApiSection />

            )}

          </div>

        </section>



        {/* ===================================================
            FOOTER
        =================================================== */}

        <footer className="settings-footer">

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
};


/* =========================================================
   SECTION HEADER
========================================================= */

const SectionHeader = ({
  icon: Icon,
  title,
  description,
}) => {
  return (
    <div className="panel-heading">

      <div className="panel-heading-icon">
        <Icon
          size={31}
          strokeWidth={1.6}
        />
      </div>

      <div>

        <h2>
          {title}
        </h2>

        <p>
          {description}
        </p>

      </div>

    </div>
  );
};


/* =========================================================
   PROFILE
========================================================= */

const ProfileSection = ({
  profile,
  updateProfile,
  onCancel,
  onSave,
}) => {
  return (
    <div className="settings-section">

      <SectionHeader
        icon={User}
        title="Profile Settings"
        description="Manage your personal and organizational information"
      />


      <div className="profile-form">


        <FormField
          label="Full Name"
          required
          type="text"
          value={profile.fullName}
          onChange={(value) =>
            updateProfile("fullName", value)
          }
        />


        <FormField
          label="Email"
          required
          type="email"
          value={profile.email}
          onChange={(value) =>
            updateProfile("email", value)
          }
        />


        <FormField
          label="Organization"
          required
          type="text"
          value={profile.organization}
          onChange={(value) =>
            updateProfile("organization", value)
          }
        />


        <SelectField
          label="Role"
          required
          value={profile.role}
          onChange={(value) =>
            updateProfile("role", value)
          }
          placeholder=""
          options={[
            "Procurement Manager",
            "Chartering Manager",
            "Logistics Manager",
            "Operations Manager",
            "Analyst",
          ]}
        />


        <FormField
          label="Phone Number"
          type="tel"
          value={profile.phone}
          onChange={(value) =>
            updateProfile("phone", value)
          }
        />

      </div>


      <ActionButtons
        onCancel={onCancel}
        onSave={onSave}
      />

    </div>
  );
};


/* =========================================================
   NOTIFICATIONS
========================================================= */

const NotificationsSection = ({
  notifications,
  toggleNotification,
  onSave,
}) => {
  return (
    <div className="settings-section">

      <SectionHeader
        icon={BellRing}
        title="Notification Settings"
        description="Choose which FreightWise events should notify you"
      />


      <div className="preference-list">


        <PreferenceRow
          icon={TrendingUp}
          title="Freight Rate Alerts"
          description="Receive alerts when forecasted freight rates move significantly."
          enabled={notifications.freightRate}
          onToggle={() =>
            toggleNotification("freightRate")
          }
        />


        <PreferenceRow
          icon={CalendarDays}
          title="Chartering Window Alerts"
          description="Get notified when a favorable chartering window is detected."
          enabled={notifications.charterWindow}
          onToggle={() =>
            toggleNotification("charterWindow")
          }
        />


        <PreferenceRow
          icon={AlertTriangle}
          title="Port Congestion Alerts"
          description="Receive alerts when congestion may affect your planned voyage."
          enabled={notifications.portCongestion}
          onToggle={() =>
            toggleNotification("portCongestion")
          }
        />


        <PreferenceRow
          icon={CloudRain}
          title="Weather & Maritime Risk"
          description="Get warnings when weather or maritime conditions may affect operations."
          enabled={notifications.weatherRisk}
          onToggle={() =>
            toggleNotification("weatherRisk")
          }
        />


        <PreferenceRow
          icon={Mail}
          title="Market Digest"
          description="Receive a periodic summary of freight market movements."
          enabled={notifications.marketDigest}
          onToggle={() =>
            toggleNotification("marketDigest")
          }
        />


        <PreferenceRow
          icon={Activity}
          title="Model & System Updates"
          description="Receive important updates about forecasting models and system changes."
          enabled={notifications.modelUpdates}
          onToggle={() =>
            toggleNotification("modelUpdates")
          }
        />

      </div>


      <ActionButtons
        onSave={onSave}
        hideCancel
      />

    </div>
  );
};


/* =========================================================
   FORECASTING
========================================================= */

const ForecastingSection = ({
  forecasting,
  updateForecasting,
  onSave,
}) => {
  return (
    <div className="settings-section">

      <SectionHeader
        icon={LineChart}
        title="Forecasting Preferences"
        description="Configure how FreightWise presents freight intelligence"
      />


      <div className="settings-grid">


        <SelectField
          label="Forecast Horizon"
          value={forecasting.horizon}
          onChange={(value) =>
            updateForecasting("horizon", value)
          }
          options={[
            "7",
            "14",
            "30",
            "60",
            "90",
          ]}
          suffix="days"
        />


        <SelectField
          label="Update Frequency"
          value={forecasting.frequency}
          onChange={(value) =>
            updateForecasting("frequency", value)
          }
          options={[
            "Daily",
            "Weekly",
            "Monthly",
          ]}
        />


        <SelectField
          label="Freight Benchmark"
          value={forecasting.benchmark}
          onChange={(value) =>
            updateForecasting("benchmark", value)
          }
          placeholder=""
          options={[
            "Baltic Dry Index",
            "Capesize Index",
            "Panamax Index",
            "Supramax Index",
          ]}
        />


        <SelectField
          label="Minimum Confidence"
          value={forecasting.confidence}
          onChange={(value) =>
            updateForecasting("confidence", value)
          }
          options={[
            "60",
            "70",
            "80",
            "90",
          ]}
          suffix="%"
        />


        <SelectField
          label="Forecast Region"
          value={forecasting.region}
          onChange={(value) =>
            updateForecasting("region", value)
          }
          placeholder=""
          options={[
            "East Coast India",
            "West Coast India",
            "India",
            "Global",
          ]}
        />

      </div>


      <div className="info-card">

        <Gauge size={20} />

        <div>

          <strong>
            Forecast confidence
          </strong>

          <p>
            Higher confidence thresholds reduce low-confidence
            recommendations from appearing in decision views.
          </p>

        </div>

      </div>


      <ActionButtons
        onSave={onSave}
        hideCancel
      />

    </div>
  );
};


/* =========================================================
   DEFAULT VOYAGE SETTINGS
========================================================= */

const VoyageDefaultsSection = ({
  values,
  updateValue,
  onSave,
}) => {
  return (
    <div className="settings-section">

      <SectionHeader
        icon={Compass}
        title="Default Voyage Settings"
        description="Set defaults used when creating and evaluating voyages"
      />


      <div className="settings-grid">


        <SelectField
          label="Default Cargo Type"
          value={values.cargo}
          onChange={(value) =>
            updateValue("cargo", value)
          }
          placeholder=""
          options={[
            "Coal",
            "Iron Ore",
            "Limestone",
            "Fertilizer",
            "Other Bulk Cargo",
          ]}
        />


        <SelectField
          label="Default Origin Country"
          value={values.origin}
          onChange={(value) =>
            updateValue("origin", value)
          }
          placeholder=""
          options={[
            "Australia",
            "Indonesia",
            "South Africa",
            "Brazil",
            "Other",
          ]}
        />


        <SelectField
          label="Default Destination"
          value={values.destination}
          onChange={(value) =>
            updateValue("destination", value)
          }
          options={[
            "East Coast India",
            "West Coast India",
            "India",
          ]}
        />


        <SelectField
          label="Preferred Vessel Class"
          value={values.vesselClass}
          onChange={(value) =>
            updateValue("vesselClass", value)
          }
          placeholder=""
          options={[
            "Capesize",
            "Panamax",
            "Supramax",
            "Handysize",
          ]}
        />


        <SelectField
          label="Arrival Buffer"
          value={values.arrivalBuffer}
          onChange={(value) =>
            updateValue("arrivalBuffer", value)
          }
          options={[
            "0",
            "1",
            "2",
            "3",
            "5",
            "7",
          ]}
          suffix="days"
        />


        <SelectField
          label="Measurement Units"
          value={values.units}
          onChange={(value) =>
            updateValue("units", value)
          }
          options={[
            "Metric",
            "Imperial",
          ]}
        />


        <SelectField
          label="Currency"
          value={values.currency}
          onChange={(value) =>
            updateValue("currency", value)
          }
          options={[
            "USD",
            "INR",
            "EUR",
          ]}
        />

      </div>


      <ActionButtons
        onSave={onSave}
        hideCancel
      />

    </div>
  );
};


/* =========================================================
   DATA & PRIVACY
========================================================= */

const PrivacySection = ({
  privacy,
  updatePrivacy,
  onSave,
}) => {
  return (
    <div className="settings-section">

      <SectionHeader
        icon={ShieldCheck}
        title="Data & Privacy"
        description="Control how your FreightWise account data is handled"
      />


      <div className="privacy-list">


        <PreferenceRow
          icon={Activity}
          title="Product Analytics"
          description="Allow anonymous product usage data to help improve FreightWise."
          enabled={privacy.analytics}
          onToggle={() =>
            updatePrivacy(
              "analytics",
              !privacy.analytics
            )
          }
        />


        <PreferenceRow
          icon={Database}
          title="Voyage Activity History"
          description="Keep previous voyage evaluations available in your workspace."
          enabled={privacy.activityHistory}
          onToggle={() =>
            updatePrivacy(
              "activityHistory",
              !privacy.activityHistory
            )
          }
        />

      </div>


      <div className="privacy-grid">

        <div className="privacy-action-card">

          <div className="privacy-card-icon">
            <Download size={20} />
          </div>

          <div>

            <strong>
              Export Your Data
            </strong>

            <p>
              Request a copy of your FreightWise account data.
            </p>

          </div>

          <button type="button">
            Export
          </button>

        </div>


        <div className="privacy-action-card danger">

          <div className="privacy-card-icon">
            <Trash2 size={20} />
          </div>

          <div>

            <strong>
              Delete Account
            </strong>

            <p>
              Permanently remove your account and associated data.
            </p>

          </div>

          <button type="button">
            Request
          </button>

        </div>

      </div>


      <div className="retention-row">

        <div>

          <strong>
            Data Retention
          </strong>

          <p>
            Choose how long historical workspace activity is retained.
          </p>

        </div>

        <select
          value={privacy.dataRetention}
          onChange={(event) =>
            updatePrivacy(
              "dataRetention",
              event.target.value
            )
          }
        >

          <option>
            3 months
          </option>

          <option>
            6 months
          </option>

          <option>
            12 months
          </option>

          <option>
            24 months
          </option>

        </select>

      </div>


      <ActionButtons
        onSave={onSave}
        hideCancel
      />

    </div>
  );
};


/* =========================================================
   APPEARANCE
========================================================= */

const AppearanceSection = ({
  appearance,
  updateAppearance,
  onSave,
}) => {
  return (
    <div className="settings-section">

      <SectionHeader
        icon={Palette}
        title="Appearance"
        description="Customize how FreightWise looks and behaves"
      />


      <div className="appearance-options">


        <div className="appearance-block">

          <div className="appearance-title">

            <Palette size={19} />

            <div>

              <strong>
                Theme
              </strong>

              <span>
                Choose your preferred workspace theme.
              </span>

            </div>

          </div>


          <div className="theme-options">

            {[
              {
                label: "Light",
                icon: Sun,
              },
              {
                label: "Dark",
                icon: Moon,
              },
              {
                label: "System",
                icon: Monitor,
              },
            ].map((item) => {

              const Icon = item.icon;

              return (
                <button
                  key={item.label}
                  type="button"
                  className={
                    appearance.theme === item.label
                      ? "theme-option active"
                      : "theme-option"
                  }
                  onClick={() =>
                    updateAppearance(
                      "theme",
                      item.label
                    )
                  }
                >

                  <Icon size={19} />

                  <span>
                    {item.label}
                  </span>

                </button>
              );

            })}

          </div>

        </div>


        <div className="settings-grid appearance-grid">

          <SelectField
            label="Interface Density"
            value={appearance.density}
            onChange={(value) =>
              updateAppearance(
                "density",
                value
              )
            }
            options={[
              "Comfortable",
              "Compact",
              "Spacious",
            ]}
          />


          <SelectField
            label="Startup Page"
            value={appearance.startPage}
            onChange={(value) =>
              updateAppearance(
                "startPage",
                value
              )
            }
            options={[
              "Dashboard",
              "New Voyage",
              "Analysis",
              "Vessels",
            ]}
          />


          <SelectField
            label="Chart Detail"
            value={appearance.charts}
            onChange={(value) =>
              updateAppearance(
                "charts",
                value
              )
            }
            options={[
              "Simple",
              "Detailed",
              "Advanced",
            ]}
          />

        </div>

      </div>


      <ActionButtons
        onSave={onSave}
        hideCancel
      />

    </div>
  );
};


/* =========================================================
   SYSTEM & API
========================================================= */

const SystemApiSection = () => {
  return (
    <div className="settings-section">

      <SectionHeader
        icon={Database}
        title="System & API"
        description="Review FreightWise system configuration and integrations"
      />


      <div className="system-status-grid">


        <SystemStatusCard
          icon={Server}
          title="API Service"
          description="Application programming interface"
        />


        <SystemStatusCard
          icon={Activity}
          title="Decision Engine"
          description="Recommendation and optimization layer"
        />


        <SystemStatusCard
          icon={LineChart}
          title="Forecasting Engine"
          description="Freight forecasting service"
        />


        <SystemStatusCard
          icon={CloudRain}
          title="External Intelligence"
          description="Weather and maritime data integrations"
        />

      </div>


      <div className="system-info-card">

        <div className="system-info-header">

          <div className="system-info-icon">
            <KeyRound size={20} />
          </div>

          <div>

            <strong>
              API Access
            </strong>

            <p>
              API credentials and integration configuration
              can be managed from this workspace.
            </p>

          </div>

        </div>


        <div className="api-placeholder">

          <span>
            API credentials
          </span>

          <div>
            Not configured
          </div>

        </div>

      </div>


      <div className="system-version-row">

        <div>

          <span>
            Application
          </span>

          <strong>
            FreightWise
          </strong>

        </div>


        <div>

          <span>
            Model Version
          </span>

          <strong>
            Current
          </strong>

        </div>


        <div>

          <span>
            Environment
          </span>

          <strong>
            Application
          </strong>

        </div>

      </div>

    </div>
  );
};


/* =========================================================
   FORM FIELD
========================================================= */

const FormField = ({
  label,
  required,
  type = "text",
  value,
  onChange,
}) => {
  return (
    <div className="form-field">

      <label>
        {label}

        {required && (
          <span>*</span>
        )}
      </label>

      <input
        type={type}
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
      />

    </div>
  );
};


/* =========================================================
   SELECT FIELD
========================================================= */

const SelectField = ({
  label,
  required,
  value,
  onChange,
  options,
  placeholder,
  suffix,
}) => {
  return (
    <div className="form-field">

      <label>

        {label}

        {required && (
          <span>*</span>
        )}

      </label>

      <div className="select-wrapper">

        <select
          value={value}
          onChange={(event) =>
            onChange(event.target.value)
          }
        >

          {placeholder !== undefined && (
            <option
              value=""
              disabled
            >
            </option>
          )}

          {options.map((option) => (

            <option
              key={option}
              value={option}
            >
              {option}
              {suffix ? ` ${suffix}` : ""}
            </option>

          ))}

        </select>

      </div>

    </div>
  );
};


/* =========================================================
   PREFERENCE ROW
========================================================= */

const PreferenceRow = ({
  icon: Icon,
  title,
  description,
  enabled,
  onToggle,
}) => {
  return (
    <div className="preference-row">

      <div className="preference-icon">

        <Icon
          size={20}
          strokeWidth={1.7}
        />

      </div>


      <div className="preference-content">

        <strong>
          {title}
        </strong>

        <p>
          {description}
        </p>

      </div>


      <button
        type="button"
        className={`toggle ${
          enabled ? "on" : ""
        }`}
        onClick={onToggle}
        aria-label={`Toggle ${title}`}
      >

        <span></span>

      </button>

    </div>
  );
};


/* =========================================================
   SYSTEM STATUS CARD
========================================================= */

const SystemStatusCard = ({
  icon: Icon,
  title,
  description,
}) => {
  return (
    <div className="system-status-card">

      <div className="system-card-icon">
        <Icon size={21} />
      </div>

      <div className="system-card-content">

        <strong>
          {title}
        </strong>

        <p>
          {description}
        </p>

      </div>

      <div className="system-status-indicator">
        <CheckCircle2 size={14} />
        <span>
          Ready
        </span>
      </div>

    </div>
  );
};


/* =========================================================
   ACTION BUTTONS
========================================================= */

const ActionButtons = ({
  onCancel,
  onSave,
  hideCancel = false,
}) => {
  return (
    <div className="panel-actions">

      {!hideCancel && (
        <button
          type="button"
          className="cancel-button"
          onClick={onCancel}
        >

          <X size={16} />

          Cancel

        </button>
      )}


      <button
        type="button"
        className="save-settings-button"
        onClick={onSave}
      >

        <Save size={17} />

        Save Changes

      </button>

    </div>
  );
};


export default Settings;