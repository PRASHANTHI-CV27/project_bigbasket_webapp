document.addEventListener("DOMContentLoaded", () => {
  // Utility function to get CSRF token from cookie
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  // Utility function to show temporary messages
  function showTemporaryMessage(message, duration = 3000) {
    let messageDiv = document.createElement("div");
    messageDiv.textContent = message;
    messageDiv.style.position = "fixed";
    messageDiv.style.top = "20px";
    messageDiv.style.right = "20px";
    messageDiv.style.backgroundColor = "#28a745";
    messageDiv.style.color = "white";
    messageDiv.style.padding = "10px 20px";
    messageDiv.style.borderRadius = "5px";
    messageDiv.style.zIndex = "1060";
    messageDiv.style.boxShadow = "0 2px 6px rgba(0,0,0,0.3)";
    document.body.appendChild(messageDiv);

    setTimeout(() => {
      messageDiv.remove();
    }, duration);
  }

  // Sign Up
  document.getElementById("signupForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = {
      username: document.getElementById("signupName").value,
      email: document.getElementById("signupEmail").value,
      password: document.getElementById("signupPassword").value,
      role: document.getElementById("signupRole").value
    };

    let res = await fetch("/api/users/signup/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      credentials: "same-origin",
      body: JSON.stringify(data)
    });

    let result;
    try {
      result = await res.json();
    } catch (err) {
      showTemporaryMessage("Signup failed: Invalid server response", 4000);
      return;
    }

    if (res.ok) {
      showTemporaryMessage("Signup successful! Please login.", 3000);
    } else {
      showTemporaryMessage("Error: " + (result.detail || JSON.stringify(result)), 4000);
    }
  });

  // Request OTP
  // Request OTP
document.getElementById("requestOtpBtn").addEventListener("click", async () => {
  const email = document.getElementById("loginEmail").value;
  if (!email) {
    showTemporaryMessage("Please enter your email to request OTP.", 3000);
    return;
  }

  let res = await fetch("/api/users/request-otp/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken"),
    },
    credentials: "same-origin",
    body: JSON.stringify({ email }),
  });

  let result;
  try {
    result = await res.json();
  } catch (err) {
    showTemporaryMessage("Failed to request OTP: Invalid server response", 4000);
    return;
  }

  if (res.ok) {
    showTemporaryMessage("OTP sent successfully.", 4000);

    // 👇 For development only (show OTP on screen)
    if (result.otp) {
      showTemporaryMessage("OTP: " + (result.otp || "Check your email"), 6000);
    }
  } else {
    showTemporaryMessage(
      "Failed to request OTP: " + (result.detail || JSON.stringify(result)),
      4000
    );
  }
});


  // Login
   document.getElementById("loginForm").addEventListener("submit", async (e) => {
     e.preventDefault();

     const email = document.getElementById("loginEmail").value;
     const credential = document.getElementById("loginCredential").value;

     const data = { email, otp: credential };


    let res = await fetch("/api/users/login/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      credentials: "same-origin",
      body: JSON.stringify(data),
    });

    let result;
    try {
      result = await res.json();
    } catch (err) {
      showTemporaryMessage("Login failed: Invalid server response", 4000);
      return;
    }

    if (res.ok) {
      showTemporaryMessage("Login successful!", 3000);
      // Save token/session
      localStorage.setItem("token", result.tokens.access);
      localStorage.setItem("refresh", result.tokens.refresh); // refresh token

      // Redirect based on role
      if (result.role === "admin") {
        window.location.href = "/admin/";
      } else if (result.role === "vendor") {
        window.location.href = "/vendors/";
      } else {
        window.location.href = "/";
      }
    } else {
      showTemporaryMessage("Login failed: " + (result.detail || JSON.stringify(result)), 4000);
    }
  });

function updateLoginUI() {
    const token = localStorage.getItem("token");
    const loginBtn = document.querySelector(".login-btn");

    if (!loginBtn) return;

    if (token) {
      loginBtn.textContent = "Logout";
      loginBtn.removeAttribute("data-bs-toggle");
      loginBtn.removeAttribute("data-bs-target");
      loginBtn.onclick = () => {
        localStorage.removeItem("token");
        localStorage.removeItem("refresh");  // ✅ clear refresh token too
        showTemporaryMessage("Logged out successfully", 3000);
        updateLoginUI();
        window.location.href = "/";
      };
    } else {
      loginBtn.textContent = "Login / Signup";
      loginBtn.setAttribute("data-bs-toggle", "modal");
      loginBtn.setAttribute("data-bs-target", "#authModal");
      loginBtn.onclick = null;
    }
  }

  // ---- After Login Success ----
 function handleLoginSuccess(tokens) {
  if (tokens.access) {
    localStorage.setItem("token", tokens.access);
  }
  if (tokens.refresh) {
    localStorage.setItem("refresh", tokens.refresh);
  }
  updateLoginUI();
  const modal = bootstrap.Modal.getInstance(
    document.getElementById("authModal")
  );
  if (modal) modal.hide();
}


  // Call on page load
  updateLoginUI();

  // ---- Toggle between Login and Signup ----
  const loginLink = document.getElementById("showLogin");
  const signupLink = document.getElementById("showSignup");
  const loginBox = document.getElementById("loginBox");
  const signupBox = document.getElementById("signupBox");

  if (loginLink && signupLink && loginBox && signupBox) {
    // Show login form
    loginLink.addEventListener("click", (e) => {
      e.preventDefault();
      loginBox.classList.remove("d-none");
      signupBox.classList.add("d-none");
      loginLink.classList.add("active");
      signupLink.classList.remove("active");
    });

    // Show signup form
    signupLink.addEventListener("click", (e) => {
      e.preventDefault();
      signupBox.classList.remove("d-none");
      loginBox.classList.add("d-none");
      signupLink.classList.add("active");
      loginLink.classList.remove("active");
    });
  }



});

async function getAccessToken() {
  let access = localStorage.getItem("access");
  const refresh = localStorage.getItem("refresh");

  // If access exists, try it
  if (access) return access;

  // If no refresh, user must login again
  if (!refresh) return null;

  // Refresh the token
  const res = await fetch("/api/token/refresh/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (res.ok) {
    const data = await res.json();
    localStorage.setItem("access", data.access);
    return data.access;
  } else {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    return null;
  }
}
