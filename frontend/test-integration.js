/**
 * frontend/test-integration.js
 * End-to-end node integration test verifying that the frontend API client
 * contracts match the running FastAPI backend responses 100%.
 */
import axios from 'axios'

const BASE_URL = 'http://127.0.0.1:8000/api/v1'

async function runTests() {
  console.log('Testing live backend connectivity at:', BASE_URL)
  let passed = 0

  // 1. Health
  try {
    const res = await axios.get(`${BASE_URL}/health`)
    if (res.status === 200 && res.data.status === 'healthy') {
      console.log('✔ 1. Health check passed:', res.data.version, res.data.tier_available)
      passed++
    }
  } catch (e) {
    console.error('✘ 1. Health check failed:', e.message)
  }

  // 2. Cohort List (IPL Batters)
  try {
    const res = await axios.get(`${BASE_URL}/players/IPL/Batter`)
    if (res.status === 200 && res.data.players.length > 0) {
      console.log(`✔ 2. Cohort list passed: ${res.data.players.length} players found in ${res.data.cohort}`)
      passed++
    }
  } catch (e) {
    console.error('✘ 2. Cohort list failed:', e.message)
  }

  // 3. Player Profile (Rinku Singh)
  try {
    const res = await axios.get(`${BASE_URL}/players/IPL/Batter/Rinku%20Singh`)
    if (res.status === 200 && res.data.player_name === 'Rinku Singh' && res.data.cpri_score === 89.03) {
      console.log('✔ 3. Player profile passed: Rinku Singh CPRI =', res.data.cpri_score)
      passed++
    }
  } catch (e) {
    console.error('✘ 3. Player profile failed:', e.message)
  }

  // 4. Player Splits
  try {
    const res = await axios.get(`${BASE_URL}/players/IPL/Batter/Rinku%20Singh/splits`)
    if (res.status === 200 && res.data.innings_phase_splits?.death?.strike_rate) {
      console.log('✔ 4. Player splits passed: Death SR =', res.data.innings_phase_splits.death.strike_rate)
      passed++
    }
  } catch (e) {
    console.error('✘ 4. Player splits failed:', e.message)
  }

  // 5. Scouting Report
  try {
    const res = await axios.get(`${BASE_URL}/scouting/report/IPL/Batter/Rinku%20Singh`)
    if (res.status === 200 && res.data.verified === true && res.data.response.includes('Rinku Singh')) {
      console.log('✔ 5. Scouting report passed:', res.data.tier_used)
      passed++
    }
  } catch (e) {
    console.error('✘ 5. Scouting report failed:', e.message)
  }

  // 6. Pressure Explanation
  try {
    const res = await axios.get(`${BASE_URL}/scouting/pressure/IPL/Batter/Rinku%20Singh`)
    if (res.status === 200 && res.data.verified === true) {
      console.log('✔ 6. Pressure explanation passed: Verified =', res.data.verified)
      passed++
    }
  } catch (e) {
    console.error('✘ 6. Pressure explanation failed:', e.message)
  }

  // 7. Player Comparison
  try {
    const res = await axios.post(`${BASE_URL}/scouting/compare`, {
      scope: 'IPL',
      role: 'Batter',
      player_a: 'Rinku Singh',
      player_b: 'Suryakumar Yadav',
    })
    if (res.status === 200 && res.data.structured_comparison?.deltas_a_minus_b) {
      console.log('✔ 7. Player comparison passed: CPRI Delta =', res.data.structured_comparison.deltas_a_minus_b.cpri_delta)
      passed++
    }
  } catch (e) {
    console.error('✘ 7. Player comparison failed:', e.message)
  }

  // 8. Matchup Analysis
  try {
    const res = await axios.get(`${BASE_URL}/scouting/matchup/IPL/Virat%20Kohli/Jasprit%20Bumrah`)
    if (res.status === 200 && res.data.h2h_data?.balls_faced >= 18) {
      console.log('✔ 8. Matchup passed: Virat vs Bumrah balls =', res.data.h2h_data.balls_faced, 'Small sample =', res.data.is_small_sample)
      passed++
    }
  } catch (e) {
    console.error('✘ 8. Matchup failed:', e.message)
  }

  // 9. AI Terminal Ask
  try {
    const res = await axios.post(`${BASE_URL}/scouting/ask`, {
      query: 'Why is Rinku Singh ranked highly under IPL pressure?',
      scope: 'IPL',
    })
    if (res.status === 200 && res.data.answer.length > 50) {
      console.log('✔ 9. AI Terminal QA passed: Response length =', res.data.answer.length)
      passed++
    }
  } catch (e) {
    console.error('✘ 9. AI Terminal QA failed:', e.message)
  }

  console.log(`\n========================================`)
  console.log(`FRONTEND-BACKEND INTEGRATION: ${passed}/9 TESTS PASSED`)
  console.log(`========================================`)

  if (passed === 9) {
    process.exit(0)
  } else {
    process.exit(1)
  }
}

runTests()
