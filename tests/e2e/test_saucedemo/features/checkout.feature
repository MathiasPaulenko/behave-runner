Feature: Saucedemo Checkout

  @smoke
  Scenario: Complete checkout
    Given I am logged in as a standard user
    And I have added the first product to the cart
    When I go to the cart
    And I checkout with first name "John" last name "Doe" and zip "12345"
    And I finish the checkout
    Then I should see the checkout complete message
