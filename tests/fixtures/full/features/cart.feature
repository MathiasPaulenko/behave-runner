Feature: Shopping cart
  As a shopper
  I want to manage my cart
  So that I can purchase items

  @smoke
  Scenario: Add item to cart
    Given I have an empty cart
    When I add a product priced at 10
    Then my cart should have 1 items
    And the cart total should be 10

  @smoke @fast
  Scenario: Remove item from cart
    Given I have a cart with 2 items
    When I remove the first item
    Then my cart should have 1 items

  @regression
  Scenario: Cart total with multiple items
    Given I have an empty cart
    When I add a product priced at 10
    And I add a product priced at 20
    And I add a product priced at 5
    Then the cart total should be 35
    And my cart should have 3 items

  @slow
  Scenario: Apply discount code
    Given I have a cart with items totaling 100
    When I apply a discount of 20 percent
    Then the cart total should be 80
