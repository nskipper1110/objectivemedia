/*
 * copyright (c) 2013 Nathan Skipper, Montgomery Technology, Inc.
 *
 * This file is part of ObjectiveMedia (http://nskipper1110.github.com/objectivemedia).
 *
 * ObjectiveMedia is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * ObjectiveMedia is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with ObjectiveMedia; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
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
                java.util.Map<String, String> EnvVars = System.getenv();
                
                String archtype = System.getProperty("os.arch");
                String userhome = System.getProperty("user.home");
                String libPath64 = userhome + "/objectivemedia/linux/ObjectiveMedia/dist/Debug64/lin64/";
                String libFile64 = "ObjectiveMedia_lin64.so";
                String libPath32 = userhome + "/objectivemedia/linux/objectivemedia/dist/debug/lin32/";
                String libFile32 = "ObjectiveMedia_lin32.so";
                if(EnvVars.containsKey("OBJECTIVEMEDIAPATH64"))
                    libPath64 = EnvVars.get("OBJECTIVEMEDIAPATH64");
                if(EnvVars.containsKey("OBJECTIVEMEDIAPATH32"))
                    libPath32 = EnvVars.get("OBJECTIVEMEDIAPATH32");
                if(EnvVars.containsKey("OBJECTIVEMEDIAFILE64"))
                    libFile64 = EnvVars.get("OBJECTIVEMEDIAFILE64");
                if(EnvVars.containsKey("OBJECTIVEMEDIAFILE32"))
                    libFile32 = EnvVars.get("OBJECTIVEMEDIAFILE32");
                System.out.println("ObjectiveMediaSample Running...");
                System.out.println("Architecture " + archtype);
                System.out.println("Environment Variables: ");
                System.out.println(EnvVars.toString());
                if(archtype.contains("amd64")){
                    System.out.println("Loading " + libFile64 + " from " + libPath64);
                    Primitives.LibraryPath = libPath64;
                    Primitives.NativeLibraries.add(libFile64);

                }
                else{
                    System.out.println("Loading " + libFile32 + " from " + libPath32);
                    Primitives.LibraryPath = libPath32;
                    Primitives.NativeLibraries.add(libFile32);
                }
                
                Primitives.InitializePrimitives();
                MainForm fm = new MainForm();
                fm.setSize(680, 600);
                fm.setVisible(true);
                fm.setTitle("ObjectiveMedia Sample App");
            }
        });
    }
}
