/**
 * Unit Tests for Mode Selection Component
 * Tests the selectMode function and mode selection logic
 * Validates Requirements 1.4, 1.5
 */

describe('Mode Selection Component', () => {
  
  beforeEach(() => {
    // Reset app state before each test
    resetAppState();
    clearSessionData();
    
    // Mock DOM elements
    document.body.innerHTML = `
      <div id="app-container"></div>
      <div id="toast-container"></div>
    `;
    
    // Clear history
    history.replaceState(null, '', '/');
    
    // Clear analytics
    sessionStorage.removeItem('evalgenius_analytics');
  });
  
  describe('selectMode()', () => {
    
    describe('Validation', () => {
      it('should reject null mode parameter', () => {
        selectMode(null);
        
        expect(appState.currentMode).to.be.null;
        expect(appState.currentScreen).to.equal(SCREENS.MODE_SELECTION);
      });
      
      it('should reject undefined mode parameter', () => {
        selectMode(undefined);
        
        expect(appState.currentMode).to.be.null;
        expect(appState.currentScreen).to.equal(SCREENS.MODE_SELECTION);
      });
      
      it('should reject non-string mode parameter', () => {
        selectMode(123);
        
        expect(appState.currentMode).to.be.null;
        expect(appState.currentScreen).to.equal(SCREENS.MODE_SELECTION);
      });
      
      it('should reject invalid mode value', () => {
        selectMode('invalid-mode');
        
        expect(appState.currentMode).to.be.null;
        expect(appState.currentScreen).to.equal(SCREENS.MODE_SELECTION);
      });
      
      it('should show error toast for invalid mode', () => {
        selectMode('invalid-mode');
        
        const toastContainer = document.getElementById('toast-container');
        expect(toastContainer.children.length).to.be.greaterThan(0);
        expect(toastContainer.innerHTML).to.include('Invalid mode');
      });
    });
    
    describe('Manual Mode Selection', () => {
      it('should set mode to manual', () => {
        selectMode(EVALUATION_MODES.MANUAL);
        
        expect(appState.currentMode).to.equal(EVALUATION_MODES.MANUAL);
      });
      
      it('should navigate to manual workflow screen', () => {
        selectMode(EVALUATION_MODES.MANUAL);
        
        expect(appState.currentScreen).to.equal(SCREENS.MANUAL_WORKFLOW);
      });
      
      it('should reset session data', () => {
        // Add some data
        appState.uploadedFiles.omrSheets = [new File([''], 'test.jpg')];
        appState.results.students = [{ id: 1 }];
        
        selectMode(EVALUATION_MODES.MANUAL);
        
        expect(appState.uploadedFiles.omrSheets).to.deep.equal([]);
        expect(appState.results.students).to.deep.equal([]);
      });
      
      it('should show success toast', () => {
        selectMode(EVALUATION_MODES.MANUAL);
        
        const toastContainer = document.getElementById('toast-container');
        expect(toastContainer.children.length).to.be.greaterThan(0);
        expect(toastContainer.innerHTML).to.include('Manual evaluation mode selected');
      });
      
      it('should persist mode in session storage', () => {
        selectMode(EVALUATION_MODES.MANUAL);
        
        const saved = JSON.parse(sessionStorage.getItem('evalgenius_state'));
        expect(saved.currentMode).to.equal(EVALUATION_MODES.MANUAL);
      });
    });
    
    describe('AI Mode Selection', () => {
      it('should set mode to AI', () => {
        selectMode(EVALUATION_MODES.AI);
        
        expect(appState.currentMode).to.equal(EVALUATION_MODES.AI);
      });
      
      it('should navigate to AI workflow phase 1 screen', () => {
        selectMode(EVALUATION_MODES.AI);
        
        expect(appState.currentScreen).to.equal(SCREENS.AI_WORKFLOW_PHASE1);
      });
      
      it('should reset session data', () => {
        // Add some data
        appState.uploadedFiles.questionPaper = new File([''], 'qp.pdf');
        appState.answerKeys.ai.A = { '1': 'A' };
        
        selectMode(EVALUATION_MODES.AI);
        
        expect(appState.uploadedFiles.questionPaper).to.be.null;
        expect(appState.answerKeys.ai.A).to.deep.equal({});
      });
      
      it('should show success toast', () => {
        selectMode(EVALUATION_MODES.AI);
        
        const toastContainer = document.getElementById('toast-container');
        expect(toastContainer.children.length).to.be.greaterThan(0);
        expect(toastContainer.innerHTML).to.include('AI evaluation mode selected');
      });
      
      it('should persist mode in session storage', () => {
        selectMode(EVALUATION_MODES.AI);
        
        const saved = JSON.parse(sessionStorage.getItem('evalgenius_state'));
        expect(saved.currentMode).to.equal(EVALUATION_MODES.AI);
      });
    });
    
    describe('Mode Re-selection', () => {
      it('should handle selecting same mode twice', () => {
        selectMode(EVALUATION_MODES.MANUAL);
        const firstScreen = appState.currentScreen;
        
        selectMode(EVALUATION_MODES.MANUAL);
        
        expect(appState.currentScreen).to.equal(firstScreen);
        expect(appState.currentMode).to.equal(EVALUATION_MODES.MANUAL);
      });
      
      it('should navigate to workflow even if already in mode', () => {
        appState.currentMode = EVALUATION_MODES.MANUAL;
        appState.currentScreen = SCREENS.MODE_SELECTION;
        
        selectMode(EVALUATION_MODES.MANUAL);
        
        expect(appState.currentScreen).to.equal(SCREENS.MANUAL_WORKFLOW);
      });
    });
    
    describe('Analytics Logging', () => {
      it('should log mode selection event', () => {
        selectMode(EVALUATION_MODES.MANUAL);
        
        const analytics = JSON.parse(sessionStorage.getItem('evalgenius_analytics'));
        expect(analytics).to.be.an('array');
        expect(analytics.length).to.equal(1);
        expect(analytics[0].event).to.equal('mode_selected');
        expect(analytics[0].mode).to.equal(EVALUATION_MODES.MANUAL);
      });
      
      it('should include timestamp in analytics', () => {
        selectMode(EVALUATION_MODES.MANUAL);
        
        const analytics = JSON.parse(sessionStorage.getItem('evalgenius_analytics'));
        expect(analytics[0].timestamp).to.be.a('string');
        expect(new Date(analytics[0].timestamp).toString()).to.not.equal('Invalid Date');
      });
      
      it('should append to existing analytics', () => {
        selectMode(EVALUATION_MODES.MANUAL);
        selectMode(EVALUATION_MODES.AI);
        
        const analytics = JSON.parse(sessionStorage.getItem('evalgenius_analytics'));
        expect(analytics.length).to.equal(2);
        expect(analytics[0].mode).to.equal(EVALUATION_MODES.MANUAL);
        expect(analytics[1].mode).to.equal(EVALUATION_MODES.AI);
      });
    });
    
    describe('Error Handling', () => {
      it('should handle errors gracefully', () => {
        // Mock navigateTo to throw error
        const originalNavigateTo = window.navigateTo;
        window.navigateTo = () => {
          throw new Error('Navigation error');
        };
        
        selectMode(EVALUATION_MODES.MANUAL);
        
        // Should show error toast
        const toastContainer = document.getElementById('toast-container');
        expect(toastContainer.innerHTML).to.include('error occurred');
        
        window.navigateTo = originalNavigateTo;
      });
      
      it('should not crash on analytics logging failure', () => {
        // Mock sessionStorage to throw error
        const originalSetItem = sessionStorage.setItem;
        sessionStorage.setItem = () => {
          throw new Error('Storage error');
        };
        
        // Should not throw
        expect(() => selectMode(EVALUATION_MODES.MANUAL)).to.not.throw();
        
        sessionStorage.setItem = originalSetItem;
      });
    });
    
    describe('State Persistence (Requirement 1.5)', () => {
      it('should persist selected mode for evaluation session', () => {
        selectMode(EVALUATION_MODES.MANUAL);
        
        // Simulate page reload by restoring state
        const saved = sessionStorage.getItem('evalgenius_state');
        expect(saved).to.not.be.null;
        
        const state = JSON.parse(saved);
        expect(state.currentMode).to.equal(EVALUATION_MODES.MANUAL);
      });
      
      it('should maintain mode across screen changes', () => {
        selectMode(EVALUATION_MODES.AI);
        
        // Navigate to another screen
        showScreen(SCREENS.AI_WORKFLOW_PHASE2);
        
        expect(appState.currentMode).to.equal(EVALUATION_MODES.AI);
      });
      
      it('should persist mode in session storage after navigation', () => {
        selectMode(EVALUATION_MODES.MANUAL);
        
        const saved = JSON.parse(sessionStorage.getItem('evalgenius_state'));
        expect(saved.currentMode).to.equal(EVALUATION_MODES.MANUAL);
        expect(saved.currentScreen).to.equal(SCREENS.MANUAL_WORKFLOW);
      });
    });
    
    describe('Navigation (Requirement 1.4)', () => {
      it('should navigate to corresponding workflow for manual mode', () => {
        selectMode(EVALUATION_MODES.MANUAL);
        
        expect(appState.currentScreen).to.equal(SCREENS.MANUAL_WORKFLOW);
      });
      
      it('should navigate to corresponding workflow for AI mode', () => {
        selectMode(EVALUATION_MODES.AI);
        
        expect(appState.currentScreen).to.equal(SCREENS.AI_WORKFLOW_PHASE1);
      });
      
      it('should update browser history', () => {
        selectMode(EVALUATION_MODES.MANUAL);
        
        expect(history.state).to.deep.equal({ screen: SCREENS.MANUAL_WORKFLOW });
      });
      
      it('should update URL hash', () => {
        selectMode(EVALUATION_MODES.AI);
        
        expect(window.location.hash).to.equal(`#${SCREENS.AI_WORKFLOW_PHASE1}`);
      });
    });
  });
  
  describe('logModeSelection()', () => {
    it('should log to console', () => {
      const originalLog = console.log;
      let logged = false;
      console.log = (message) => {
        if (message.includes('Mode selected')) {
          logged = true;
        }
      };
      
      logModeSelection(EVALUATION_MODES.MANUAL);
      
      expect(logged).to.be.true;
      console.log = originalLog;
    });
    
    it('should store analytics data', () => {
      logModeSelection(EVALUATION_MODES.MANUAL);
      
      const analytics = JSON.parse(sessionStorage.getItem('evalgenius_analytics'));
      expect(analytics).to.be.an('array');
      expect(analytics[0].event).to.equal('mode_selected');
    });
  });
  
  describe('Integration Tests', () => {
    it('should complete full mode selection flow', () => {
      // Start at mode selection
      expect(appState.currentScreen).to.equal(SCREENS.MODE_SELECTION);
      expect(appState.currentMode).to.be.null;
      
      // Select manual mode
      selectMode(EVALUATION_MODES.MANUAL);
      
      // Verify state
      expect(appState.currentMode).to.equal(EVALUATION_MODES.MANUAL);
      expect(appState.currentScreen).to.equal(SCREENS.MANUAL_WORKFLOW);
      
      // Verify persistence
      const saved = JSON.parse(sessionStorage.getItem('evalgenius_state'));
      expect(saved.currentMode).to.equal(EVALUATION_MODES.MANUAL);
      
      // Verify analytics
      const analytics = JSON.parse(sessionStorage.getItem('evalgenius_analytics'));
      expect(analytics[0].mode).to.equal(EVALUATION_MODES.MANUAL);
    });
    
    it('should handle mode switching', () => {
      // Select manual mode
      selectMode(EVALUATION_MODES.MANUAL);
      expect(appState.currentMode).to.equal(EVALUATION_MODES.MANUAL);
      
      // Switch to AI mode
      selectMode(EVALUATION_MODES.AI);
      expect(appState.currentMode).to.equal(EVALUATION_MODES.AI);
      expect(appState.currentScreen).to.equal(SCREENS.AI_WORKFLOW_PHASE1);
      
      // Verify analytics has both events
      const analytics = JSON.parse(sessionStorage.getItem('evalgenius_analytics'));
      expect(analytics.length).to.equal(2);
    });
  });
});
