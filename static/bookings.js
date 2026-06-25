// Generative AI Sales Agent - Bookings Dashboard JS Engine

const bookingsTableBody = document.getElementById('bookingsTableBody');
const bookingCount = document.getElementById('bookingCount');
const searchBookings = document.getElementById('searchBookings');
const clearAllBookingsBtn = document.getElementById('clearAllBookingsBtn');

// Helper to escape HTML and prevent Cross-site Scripting (XSS)
function escapeHTML(str) {
  if (!str) return '';
  return str.replace(/[&<>'"]/g, 
    tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag)
  );
}

// Load bookings list
async function fetchBookings() {
  try {
    const response = await fetch(`/api/bookings?_t=${Date.now()}`);
    if (!response.ok) throw new Error("Could not fetch bookings list.");

    const bookings = await response.json();
    renderBookingsTable(bookings);
    updateDashboardMetrics(bookings);
  } catch (err) {
    console.error("Error fetching bookings:", err);
  }
}

// Update upper dashboard metric cards
function updateDashboardMetrics(bookings) {
  const total = bookings.length;
  const pythonCount = bookings.filter(b => (b.course_name || "").toLowerCase().includes("python")).length;
  const javaCount = bookings.filter(b => (b.course_name || "").toLowerCase().includes("java")).length;
  
  const mTotal = document.getElementById('metricTotal');
  const mPython = document.getElementById('metricPython');
  const mJava = document.getElementById('metricJava');
  
  if (mTotal) mTotal.textContent = total;
  if (mPython) mPython.textContent = pythonCount;
  if (mJava) mJava.textContent = javaCount;
}

// Render bookings table
function renderBookingsTable(bookings) {
  bookingsTableBody.innerHTML = "";
  
  const query = searchBookings.value.toLowerCase().trim();
  
  // Filter bookings based on search query
  const filtered = bookings.filter(b => {
    const name = (b.student_name || "").toLowerCase();
    const phone = (b.student_phone || "").toLowerCase();
    const course = (b.course_name || "").toLowerCase();
    const day = (b.demo_date || "").toLowerCase();
    return name.includes(query) || phone.includes(query) || course.includes(query) || day.includes(query);
  });

  bookingCount.textContent = `${filtered.length} Bookings`;

  if (filtered.length === 0) {
    bookingsTableBody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center py-4 text-muted">No student bookings found matching filter.</td>
      </tr>
    `;
    return;
  }

  // Reverse list to show newest first
  filtered.reverse().forEach(b => {
    const tr = document.createElement('tr');
    
    // Highlight if booking is confirmed
    const statusClass = b.booking_status === 'confirmed' ? 'badge-status-confirmed' : '';
    const deleteId = b.booking_id || b.student_phone;
    
    // SECURE FIX: Run escapeHTML on all interpolated user inputs to prevent XSS payloads
    const escapedName = escapeHTML(b.student_name);
    const escapedPhone = escapeHTML(b.student_phone);
    const escapedCourse = escapeHTML(b.course_name);
    const escapedDate = escapeHTML(b.demo_date);
    const escapedTime = escapeHTML(b.demo_time);
    const escapedBookingDate = escapeHTML(b.booking_date);
    const escapedBookingTime = escapeHTML(b.booking_time);
    const escapedStatus = escapeHTML(b.booking_status);
    
    tr.innerHTML = `
      <td><strong>${escapedName || 'N/A'}</strong></td>
      <td>${escapedPhone || 'N/A'}</td>
      <td>${escapedCourse || 'N/A'}</td>
      <td>${escapedDate || 'N/A'}</td>
      <td>${escapedTime || 'N/A'}</td>
      <td>${escapedBookingDate || '-'} ${escapedBookingTime || ''}</td>
      <td><span class="badge-status ${statusClass}">${escapedStatus || 'N/A'}</span></td>
      <td>
        <button class="btn-delete-row" data-id="${escapeHTML(deleteId)}" data-name="${escapedName || 'this candidate'}" title="Delete Booking">
          <i class="fa-solid fa-trash-can"></i>
        </button>
      </td>
    `;
    bookingsTableBody.appendChild(tr);
  });

  // Attach delete events to buttons
  document.querySelectorAll('.btn-delete-row').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const id = btn.getAttribute('data-id');
      const name = btn.getAttribute('data-name');
      if (confirm(`Are you sure you want to delete the booking for ${name}?`)) {
        await deleteBooking(id);
      }
    });
  });
}

// Delete specific student booking
async function deleteBooking(phone) {
  try {
    const response = await fetch(`/api/bookings/${encodeURIComponent(phone)}`, {
      method: 'DELETE'
    });
    if (response.ok) {
      fetchBookings();
    } else {
      alert("Failed to delete booking.");
    }
  } catch (err) {
    alert("Network error: " + err.message);
  }
}

// Clear all bookings
async function clearAllBookings() {
  if (confirm("Are you absolutely sure you want to clear ALL bookings from the database? This action is irreversible.")) {
    try {
      const response = await fetch('/api/bookings', { method: 'DELETE' });
      if (response.ok) {
        fetchBookings();
      } else {
        alert("Failed to clear database.");
      }
    } catch (err) {
      alert("Error clearing database: " + err.message);
    }
  }
}

// Set up event listeners
function setupEvents() {
  if (searchBookings) {
    searchBookings.addEventListener('input', () => {
      fetchBookings();
    });
  }

  if (clearAllBookingsBtn) {
    clearAllBookingsBtn.addEventListener('click', clearAllBookings);
  }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
  setupEvents();
  fetchBookings();
});
