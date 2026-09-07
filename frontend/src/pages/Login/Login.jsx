import React, { useState } from "react";
import {
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  BarChart3,
  Ship,
  ShieldCheck,
} from "lucide-react";

import "./Login.css";

function Login() {
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);

  const handleSubmit = (event) => {
    event.preventDefault();

    // Backend authentication will be connected here.
    console.log("FreightWise login submitted");
  };

  const handleGoogleLogin = () => {
    console.log("Google login selected");
  };

  const handleForgotPassword = () => {
    console.log("Forgot password selected");
  };

  const handleCreateAccount = () => {
    window.location.href = "/register";
  };

  return (
    <div className="login-page">

      {/* =====================================================
          LEFT SIDE
      ===================================================== */}

      <section className="login-left">

        <div className="login-left-overlay"></div>

        {/* Brand */}
        <div className="login-brand">

          <div className="login-brand-icon">
            <Ship size={58} strokeWidth={2.2} />
          </div>

          <div className="login-brand-content">

            <div className="login-brand-name">
              FREIGHTWISE
            </div>

            <div className="login-brand-subtitle">
              AI-Powered Freight &amp; Chartering Intelligence
              <br />
              for India's East Coast
            </div>

          </div>

        </div>


        {/* Top-right message on image */}
        <div className="left-top-message">

          <span className="left-top-line"></span>

          <div>
            India's East Coast
            <br />
            Stronger Trade
            <br />
            Brighter Tomorrow
          </div>

        </div>


        {/* Hero heading */}
        <div className="login-hero-text">

          <h1>
            Right Vessel. Right Port.{" "}
            <span>Right Time.</span>
          </h1>

          <p>
            Smarter chartering decisions through freight forecasting,
            <br />
            risk analysis and voyage optimization.
          </p>

        </div>


        {/* Feature section */}
        <div className="login-features">

          {/* Feature 1 */}
          <div className="login-feature">

            <div className="feature-circle">
              <BarChart3
                size={28}
                strokeWidth={2.2}
              />
            </div>

            <div className="feature-content">

              <h3>
                AI Freight
                <br />
                Forecasting
              </h3>

              <p>
                Data-driven insights
                <br />
                for better decisions
              </p>

            </div>

          </div>


          <div className="feature-divider"></div>


          {/* Feature 2 */}
          <div className="login-feature">

            <div className="feature-circle">
              <Ship
                size={28}
                strokeWidth={2.2}
              />
            </div>

            <div className="feature-content">

              <h3>
                Vessel &amp; Port
                <br />
                Optimization
              </h3>

              <p>
                Find the best vessels,
                <br />
                routes and ports
              </p>

            </div>

          </div>


          <div className="feature-divider"></div>


          {/* Feature 3 */}
          <div className="login-feature">

            <div className="feature-circle">
              <ShieldCheck
                size={28}
                strokeWidth={2.2}
              />
            </div>

            <div className="feature-content">

              <h3>
                Risk &amp; Cost
                <br />
                Intelligence
              </h3>

              <p>
                Lower costs,
                <br />
                safer voyages.
              </p>

            </div>

          </div>

        </div>


        {/* Bottom-left tagline */}
        <div className="left-bottom-message">

          <span>
            Navigating a Smarter, Stronger India
          </span>

          <i></i>

        </div>

      </section>


      {/* =====================================================
          RIGHT SIDE
      ===================================================== */}

      <section className="login-right">

        {/* Top-right wording */}
        <div className="right-top-message">

          <strong>
            Better Decisions
          </strong>

          <br />

          for a Stronger

          <br />

          <span>
            Maritime Future.
          </span>

          <div className="right-blue-line"></div>

        </div>


        {/* =================================================
            LOGIN CARD
        ================================================= */}

        <div className="login-card">

          {/* Logo */}
          <div className="card-brand">

            <div className="card-logo">
              <Ship
                size={43}
                strokeWidth={2.1}
              />
            </div>

            <div className="card-name">
              FREIGHTWISE
            </div>

          </div>


          {/* Heading */}
          <h2>
            Welcome back
          </h2>

          <p className="card-subtitle">
            Sign in to continue to FreightWise
          </p>


          {/* =================================================
              FORM
          ================================================= */}

          <form onSubmit={handleSubmit}>

            {/* Email */}
            <div className="form-group">

              <label htmlFor="email">
                Email Address
              </label>

              <div className="input-box">

                <Mail
                  size={20}
                  strokeWidth={2}
                />

                <input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="Enter your email"
                  autoComplete="email"
                  required
                />

              </div>

            </div>


            {/* Password */}
            <div className="form-group password-group">

              <label htmlFor="password">
                Password
              </label>

              <div className="input-box">

                <Lock
                  size={20}
                  strokeWidth={2}
                />

                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                />

                <button
                  type="button"
                  className="eye-button"
                  onClick={() =>
                    setShowPassword((value) => !value)
                  }
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                >

                  {showPassword ? (
                    <EyeOff
                      size={19}
                      strokeWidth={2}
                    />
                  ) : (
                    <Eye
                      size={19}
                      strokeWidth={2}
                    />
                  )}

                </button>

              </div>

            </div>


            {/* Remember / Forgot */}
            <div className="login-options">

              <label className="remember">

                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(event) =>
                    setRememberMe(event.target.checked)
                  }
                />

                <span>
                  Remember me
                </span>

              </label>

              <button
                type="button"
                className="forgot"
                onClick={handleForgotPassword}
              >
                Forgot password?
              </button>

            </div>


            {/* Sign in */}
            <button
              type="submit"
              className="sign-in"
            >

              <span>
                Sign In
              </span>

              <ArrowRight
                size={20}
                strokeWidth={2}
              />

            </button>

          </form>


          {/* OR */}
          <div className="or-divider">

            <span></span>

            <small>
              or
            </small>

            <span></span>

          </div>


          {/* Google */}
          <button
            type="button"
            className="google-button"
            onClick={handleGoogleLogin}
          >

            <span className="google-icon">
              G
            </span>

            <span>
              Continue with Google
            </span>

          </button>


          {/* Create account */}
          <div className="create-account">

            <span>
              Don't have an account?
            </span>

            <button
              type="button"
              onClick={handleCreateAccount}
            >
              Create account
            </button>

          </div>

        </div>


        {/* =================================================
            SECURITY SECTION
            OUTSIDE THE LOGIN CARD
        ================================================= */}

        <div className="secure-access">

          <Lock
            size={16}
            strokeWidth={2}
          />

          <div>

            <strong>
              Secure enterprise access
            </strong>

            <p>
              Your voyage and procurement data is protected.
            </p>

          </div>

        </div>


        {/* =================================================
            BOTTOM RIGHT
        ================================================= */}

        <div className="right-bottom-message">

          <strong>
            Clean Oceans
          </strong>

          <br />

          Stronger Trade

          <br />

          <span>
            Brighter India
          </span>

          <div className="right-blue-line"></div>

        </div>

      </section>

    </div>
  );
}

export default Login;