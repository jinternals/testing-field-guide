package shop.e2e;

import com.microsoft.playwright.*;
import com.microsoft.playwright.options.AriaRole;

/** Page Object: the test talks about the page, not its HTML. */
class CheckoutPage {
  private final Page page;

  CheckoutPage(Page page) { this.page = page; }

  void addToCart(String product) {
    page.getByRole(AriaRole.BUTTON,
        new Page.GetByRoleOptions().setName("Add " + product))
        .click();
  }

  void checkout() { page.getByTestId("checkout").click(); }

  Locator total() { return page.getByTestId("order-total"); }
}
