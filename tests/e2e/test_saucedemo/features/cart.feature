Feature: Saucedemo Cart

  @smoke
  Scenario: Add item to cart
    Given I am logged in as a standard user
    When I add the first product to the cart
    Then the cart badge should show "1"

  Scenario: Remove item from cart
    Given I am logged in as a standard user
    And I have added the first product to the cart
    When I remove the first product from the cart
    Then the cart badge should be empty
