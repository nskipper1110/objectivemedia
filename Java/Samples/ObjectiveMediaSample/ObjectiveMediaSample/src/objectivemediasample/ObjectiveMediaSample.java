/*
 * To change this template, choose Tools | Templates
 * and open the template in the editor.
 */
package objectivemediasample;
import com.mti.primitives.Primitives;
/**
 *
 * @author nathan
 */
public class ObjectiveMediaSample {

    /**
     * @param args the command line arguments
     */
    public static void main(String[] args) {
        try {
            for (javax.swing.UIManager.LookAndFeelInfo info : javax.swing.UIManager.getInstalledLookAndFeels()) {
                if ("Nimbus".equals(info.getName())) {
                    javax.swing.UIManager.setLookAndFeel(info.getClassName());
                    break;
                }
            }
        } catch (ClassNotFoundException ex) {
            java.util.logging.Logger.getLogger(MainForm.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (InstantiationException ex) {
            java.util.logging.Logger.getLogger(MainForm.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (IllegalAccessException ex) {
            java.util.logging.Logger.getLogger(MainForm.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        } catch (javax.swing.UnsupportedLookAndFeelException ex) {
            java.util.logging.Logger.getLogger(MainForm.class.getName()).log(java.util.logging.Level.SEVERE, null, ex);
        }
        //</editor-fold>

        /* Create and display the form */
        java.awt.EventQueue.invokeLater(new Runnable() {
            public void run() {
                Primitives.LibraryPath = "C:\\objectivemedia\\build\\debug\\win64\\";
                Primitives.NativeLibraries.add("objectivemedia_win64.dll");
                Primitives.InitializePrimitives();
                MainForm fm = new MainForm();
                fm.setSize(680, 600);
                fm.setVisible(true);
                fm.setTitle("ObjectiveMedia Sample App");
            }
        });
    }
}
