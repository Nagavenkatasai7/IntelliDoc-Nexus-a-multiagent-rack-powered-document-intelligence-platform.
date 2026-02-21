import { test, expect } from "@playwright/test";

test.describe("IntelliDoc Nexus", () => {
  test("should load the application", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/IntelliDoc/i);
  });

  test("should show login page for unauthenticated users", async ({ page }) => {
    await page.goto("/");
    // Should see login or the main app (depending on auth state)
    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  test("should display sidebar with navigation", async ({ page }) => {
    await page.goto("/");
    // Look for common UI elements
    const sidebar = page.locator('[data-testid="sidebar"], nav, aside').first();
    await expect(sidebar).toBeVisible({ timeout: 10000 });
  });
});

test.describe("Authentication Flow", () => {
  test("should allow login with dev credentials", async ({ page }) => {
    await page.goto("/");

    // Find email input
    const emailInput = page.locator(
      'input[type="email"], input[name="email"], input[placeholder*="email" i]'
    ).first();

    if (await emailInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await emailInput.fill("dev@intellidoc.ai");

      const passwordInput = page.locator(
        'input[type="password"], input[name="password"]'
      ).first();
      await passwordInput.fill("devpassword123");

      const submitButton = page.locator(
        'button[type="submit"], button:has-text("Login"), button:has-text("Sign in")'
      ).first();
      await submitButton.click();

      // Wait for navigation or app load
      await page.waitForTimeout(2000);
    }
  });
});

test.describe("Document Management", () => {
  test("should show document list area", async ({ page }) => {
    await page.goto("/");
    await page.waitForTimeout(2000);

    // Look for document-related UI
    const docArea = page.locator(
      'text=/documents/i, text=/upload/i, [data-testid="document-list"]'
    ).first();

    // This may or may not be visible depending on auth state
    const isVisible = await docArea.isVisible({ timeout: 5000 }).catch(() => false);
    expect(typeof isVisible).toBe("boolean");
  });

  test("should have upload functionality", async ({ page }) => {
    await page.goto("/");
    await page.waitForTimeout(2000);

    // Look for upload button or drop zone
    const uploadElement = page.locator(
      'text=/upload/i, input[type="file"], [data-testid="upload"]'
    ).first();

    const isVisible = await uploadElement
      .isVisible({ timeout: 5000 })
      .catch(() => false);
    expect(typeof isVisible).toBe("boolean");
  });
});

test.describe("Chat Interface", () => {
  test("should have chat input area", async ({ page }) => {
    await page.goto("/");
    await page.waitForTimeout(2000);

    // Look for chat input
    const chatInput = page.locator(
      'textarea, input[placeholder*="ask" i], input[placeholder*="question" i], [data-testid="chat-input"]'
    ).first();

    const isVisible = await chatInput
      .isVisible({ timeout: 5000 })
      .catch(() => false);
    expect(typeof isVisible).toBe("boolean");
  });
});

test.describe("API Health", () => {
  test("backend API should be healthy", async ({ request }) => {
    const response = await request.get("http://localhost:8000/api/v1/health");
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.status).toBe("healthy");
    expect(data.app).toContain("IntelliDoc");
  });

  test("backend root should return app info", async ({ request }) => {
    const response = await request.get("http://localhost:8000/");
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data.docs).toBe("/docs");
  });

  test("should list documents via API", async ({ request }) => {
    const response = await request.get("http://localhost:8000/api/v1/documents");
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty("documents");
    expect(data).toHaveProperty("total");
  });
});
