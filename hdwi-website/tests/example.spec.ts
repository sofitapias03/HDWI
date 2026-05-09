import {test, expect} from '@playwright/test'

test.describe('Forecast map slider', () => {
  
  //lowest acceptable edge case
  test('shows day 0 map on load', async ({page}) => {
    await page.goto('/HDWI');

    const map = page.getByTestId('forecast-map');
    await expect(map).toBeVisible();

    const src = await map.getAttribute('src');
    expect(src).toContain('day_0');
  });


  //middle test case
  test('Show day 3 on map after moving slider one step', async ({ page}) => {
    await page.goto('/HDWI');

    const handle = page.getByTestId('day-slider').locator('.rc-slider-handle');
    await handle.focus();
    for (let x = 0; x < 3; x++){
      await handle.press('ArrowRight');
    }

    const map = page.getByTestId('forecast-map');
    const src = await map.getAttribute('src');
    expect (src).toContain('day_3');
  });



// highest acceptable edge case
  test('Show day 6 on map on rihgt most step on slider', async ({page}) => {
    await page.goto('/HDWI');

    const handle = page.getByTestId('day-slider').locator('.rc-slider-handle');
    await handle.focus();
    for(let x = 0; x < 6; x++){
      await handle.press('ArrowRight');
    }

    const map = page.getByTestId('forecast-map');
    const src = await map.getAttribute('src');
    expect (src).toContain('day_6')
  });


  //out of bouds edge case sliding more times should not even slide and the map remaisn in teh last one
  test('Sliding more than allowed steps, shows map day 8', async ({page}) => {
    await page.goto('/HDWI');

    const handle = page.getByTestId('day-slider').locator('.rc-slider-handle');
    await handle.focus();
    for (let x = 0; x < 7; x++){
      await handle.press('ArrowRight');
    }

    const map = page.getByTestId('forecast-map');
    const src = await map.getAttribute('src');
    expect (src).toContain('day_6');

  });

});