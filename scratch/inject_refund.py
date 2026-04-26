"""Inject refund modals into store.html after the bill-modal closing tag."""
import re

path = r'f:\fullclone\agrosense.io\core\templates\core\store.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

REFUND_HTML = r"""
    <!-- REFUND REQUEST MODAL -->
    <div id="refund-modal" class="modal-backdrop">
        <div class="refund-card">
            <button class="modal-close" onclick="closeRefundModal()">&#x2715;</button>
            <div class="refund-header">
                <div class="refund-icon-wrap">&#x1F4B0;</div>
                <h2>Request a Refund</h2>
                <p id="refund-order-label" style="color:#64748b;font-size:0.9rem;margin-top:4px;">Order #---</p>
            </div>
            <div class="refund-step active" id="refund-step-1">
                <h3 class="step-title">Step 1 of 3 &mdash; Why do you want a refund?</h3>
                <div class="refund-form-group">
                    <label>Select Reason</label>
                    <select id="refund-reason-cat" class="refund-select">
                        <option value="">-- Choose a reason --</option>
                        <option value="Product not received">Product not received</option>
                        <option value="Wrong item delivered">Wrong item delivered</option>
                        <option value="Damaged or Defective item">Damaged or Defective item</option>
                        <option value="Quality not as described">Quality not as described</option>
                        <option value="Changed my mind">Changed my mind</option>
                        <option value="Duplicate order">Duplicate order placed</option>
                        <option value="Other">Other</option>
                    </select>
                </div>
                <div class="refund-form-group">
                    <label>Additional Details <span style="color:#999;font-size:0.8rem;">(optional)</span></label>
                    <textarea id="refund-reason-details" class="refund-textarea" placeholder="Describe your issue in more detail..."></textarea>
                </div>
                <div class="refund-form-group">
                    <label>Upload Evidence Photo <span style="color:#999;font-size:0.8rem;">(optional)</span></label>
                    <div class="refund-upload-zone" id="refund-upload-zone" onclick="document.getElementById('refund-img-input').click()">
                        <input type="file" id="refund-img-input" accept="image/*" style="display:none" onchange="previewRefundImage(this)">
                        <p id="refund-upload-text">&#x1F4C1; Click to upload photo of item</p>
                    </div>
                </div>
                <button class="refund-next-btn" onclick="refundStep(2)">Continue &rarr;</button>
            </div>
            <div class="refund-step" id="refund-step-2">
                <h3 class="step-title">Step 2 of 3 &mdash; Where should we send the money?</h3>
                <div class="refund-amount-badge">Refund Amount: <strong id="refund-amount-display">&#x20B9;0</strong></div>
                <div class="refund-form-group">
                    <label>Refund Method</label>
                    <div class="payment-toggle">
                        <button class="pay-opt active" id="opt-upi" onclick="togglePayOpt('UPI')">UPI</button>
                        <button class="pay-opt" id="opt-bank" onclick="togglePayOpt('BANK')">Bank Transfer</button>
                    </div>
                </div>
                <div id="upi-fields">
                    <div class="refund-form-group">
                        <label>UPI ID</label>
                        <input type="text" id="refund-upi-id" class="refund-input" placeholder="yourname@upi or 9876543210@paytm">
                    </div>
                </div>
                <div id="bank-fields" style="display:none;">
                    <div class="refund-form-group">
                        <label>Account Holder Name</label>
                        <input type="text" id="refund-bank-name" class="refund-input" placeholder="Name as on bank account">
                    </div>
                    <div class="refund-form-group">
                        <label>Account Number</label>
                        <input type="text" id="refund-bank-acc" class="refund-input" placeholder="Enter account number">
                    </div>
                    <div class="refund-form-group">
                        <label>IFSC Code</label>
                        <input type="text" id="refund-bank-ifsc" class="refund-input" placeholder="e.g. SBIN0001234">
                    </div>
                </div>
                <div style="display:flex;gap:1rem;margin-top:1.5rem;">
                    <button class="refund-back-btn" onclick="refundStep(1)">&larr; Back</button>
                    <button class="refund-next-btn" onclick="refundStep(3)">Continue &rarr;</button>
                </div>
            </div>
            <div class="refund-step" id="refund-step-3">
                <h3 class="step-title">Step 3 of 3 &mdash; Review &amp; Confirm</h3>
                <div class="refund-review-box" id="refund-review-content"></div>
                <p class="refund-policy-note">&#x1F512; Your data is secure. Refund processed within <strong>24 hours</strong>.</p>
                <div style="display:flex;gap:1rem;margin-top:1.5rem;">
                    <button class="refund-back-btn" onclick="refundStep(2)">&larr; Back</button>
                    <button class="refund-submit-btn" id="refund-submit-btn" onclick="submitRefundRequest()">Submit Refund Request</button>
                </div>
            </div>
        </div>
    </div>

    <!-- REFUND SUCCESS FULL-SCREEN OVERLAY -->
    <div id="refund-success-overlay" class="refund-success-overlay">
        <div class="refund-confetti-layer" id="refund-confetti"></div>
        <div class="refund-success-card">
            <div class="success-checkmark-ring">
                <svg viewBox="0 0 80 80" width="100" height="100">
                    <circle class="checkmark-circle-anim" cx="40" cy="40" r="36" fill="none" stroke="#4caf50" stroke-width="4"/>
                    <path class="checkmark-tick-anim" d="M20 40 L34 54 L60 26" fill="none" stroke="#4caf50" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <h1 class="refund-success-title">Refund Initiated!</h1>
            <p class="refund-success-sub">Your request has been submitted successfully.</p>
            <div class="refund-success-details" id="refund-success-details"></div>
            <div class="patience-banner">
                <div class="patience-clock">&#x23F0;</div>
                <div>
                    <strong>Please allow 24 hours</strong> for the refund to reflect in your account.<br>
                    <span style="font-size:1.1rem;">Please have patience &#x2764;</span>
                </div>
            </div>
            <p class="email-sent-note">&#x1F4E7; A confirmation email has been sent to your inbox.</p>
            <button class="success-close-btn" onclick="closeRefundSuccess()">&larr; Back to Store</button>
        </div>
    </div>
"""

# Insert before the closing </div> of agrostore-container
# Find the bill-modal section end
marker = '    </div>\n</div>\n\n<style>'
if marker in content:
    content = content.replace(marker, '    </div>\n' + REFUND_HTML + '\n</div>\n\n<style>', 1)
    print("Injected refund HTML after bill-modal (Unix LF path)")
else:
    marker_crlf = '    </div>\r\n</div>\r\n\r\n<style>'
    if marker_crlf in content:
        content = content.replace(marker_crlf, '    </div>\r\n' + REFUND_HTML + '\r\n</div>\r\n\r\n<style>', 1)
        print("Injected refund HTML after bill-modal (CRLF path)")
    else:
        # Try a more flexible approach
        # Find the bill-modal div end and the closing agrostore div
        idx = content.find('id="bill-modal"')
        if idx != -1:
            # Find the next </div>\n</div> after bill-modal
            search_start = idx
            end_pattern = '</div>\n</div>'
            crlf_pattern = '</div>\r\n</div>'
            idx2 = content.find(crlf_pattern, search_start)
            if idx2 != -1:
                insert_pos = idx2 + len(crlf_pattern)
                content = content[:insert_pos] + '\r\n' + REFUND_HTML + content[insert_pos:]
                print(f"Injected at position {insert_pos}")
            else:
                idx3 = content.find(end_pattern, search_start)
                if idx3 != -1:
                    insert_pos = idx3 + len(end_pattern)
                    content = content[:insert_pos] + '\n' + REFUND_HTML + content[insert_pos:]
                    print(f"Injected at position {insert_pos} (LF)")
                else:
                    print("ERROR: Could not find insertion point")
        else:
            print("ERROR: Could not find bill-modal")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done.")
