async function loadProfilePicture() {
      const response = await fetch("/api/me/profile/picture")
      const data = await response.json()
      document.querySelectorAll('img#profile_url').forEach(img => img.src = data.url)
    }

loadProfilePicture()