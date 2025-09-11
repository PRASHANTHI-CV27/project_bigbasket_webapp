document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ auth.js loaded successfully!");

  // --- CSRF Helper ---
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  const csrftoken = getCookie("csrftoken");

  // --- Signup Form ---
  const signupForm = document.getElementById("signupForm");
  if (signupForm) {
    signupForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const name = document.getElementById("signupName").value;
      const email = document.getElementById("signupEmail").value;
      const password = document.getElementById("signupPassword").value;

      try {
        const res = await fetch("/users/api/auth/signup/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken,
          },
          body: JSON.stringify({ username: name, email, password }),
        });

        const data = await res.json();
        if (res.ok) {
          alert("✅ Signup successful! Please check your email for OTP.");
          signupForm.reset();
          // Switch to Login tab automatically
          const loginTab = document.querySelector("#login-tab");
          if (loginTab) loginTab.click();
        } else {
          alert("❌ Signup failed: " + (data.error || JSON.stringify(data)));
        }
      } catch (err) {
        console.error("Signup error:", err);
      }
    });
  }

  // --- Login Form (2-step: Request OTP → Verify OTP) ---
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const email = document.getElementById("loginEmail").value;
      const otp = document.getElementById("loginOtp").value;

      if (!otp) {
        // Step 1: Request OTP
        try {
          const res = await fetch("/users/api/auth/login/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrftoken,
            },
            body: JSON.stringify({ email }),
          });
          const data = await res.json();
          if (res.ok) {
            alert("📩 OTP sent! Please check your email.");
          } else {
            alert("❌ Login failed: " + (data.error || JSON.stringify(data)));
          }
        } catch (err) {
          console.error("Login error:", err);
        }
      } else {
        // Step 2: Verify OTP
        try {
          const res = await fetch("/users/api/auth/verify-otp/", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": csrftoken,
            },
            body: JSON.stringify({ email, otp }),
          });
          const data = await res.json();
          if (res.ok) {
            alert("✅ Login successful!");
            location.reload(); // refresh to update header button → Logout
          } else {
            alert("❌ OTP verification failed: " + (data.error || JSON.stringify(data)));
          }
        } catch (err) {
          console.error("OTP verify error:", err);
        }
      }
    });
  }
});
